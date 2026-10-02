#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gh-fetch.py — opc-track-lab 案例活取器（只抓公开仓库原文，AI 在对话里按需引用切片）

子命令:
  cases   [--edition main|programmer|game|archive|all] [--track 关键词] [--stats] [--force] [--limit N]
  awesome [关键词] [--limit N]
  raw     OWNER/REPO/路径 [--branch master] [--save 文件名]
  check                                     探测各镜像存活
  --update-self                             从 OPC_SKILL_REPO 更新技能自身（可选）

镜像链（可用环境变量 OPC_GH_MIRRORS 覆盖，逗号分隔，模板变量 {repo} {branch} {path}，direct=直连）:
  1 直连 raw.githubusercontent.com          （翻墙/海外用户）
  2-4 jsDelivr CDN（cdn/fastly/gcore 三域）  （国内一般环境，实测最稳）
  5 gh-proxy.com                             （社区代理）
  6-7 ghfast.top / ghproxy.net               （社区代理，2026-10 本机实测不可用，保留备换）
失败兜底: AI 会话内自带网页读取工具直接读原文 URL；再不行用旧缓存或无案例推演（不阻塞）。
缓存: 工作目录 opc-doc/case-cache/，超过 7 天提示刷新（--force 强制）。
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_1C7 = "1c7/chinese-independent-developer"
REPO_AWESOME = "sindresorhus/awesome"
PROBE_REPO, PROBE_PATH = "easychen/opc-methodology", "book.toml"
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_MIRRORS = ",".join([
    "direct",
    "https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}",
    "https://fastly.jsdelivr.net/gh/{repo}@{branch}/{path}",
    "https://gcore.jsdelivr.net/gh/{repo}@{branch}/{path}",
    "https://gh-proxy.com/https://raw.githubusercontent.com/{repo}/{branch}/{path}",
    "https://ghfast.top/https://raw.githubusercontent.com/{repo}/{branch}/{path}",
    "https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{branch}/{path}",
])

# 1c7 各版面文件路径：.github/pages/ 为当前布局，其余为历史布局回退
EDITIONS = {
    "main":       ["README.md"],
    "programmer": [".github/pages/README-Programmer-Edition.md", "README-Programmer-Edition.md", "pages/README-Programmer-Edition.md"],
    "game":       [".github/pages/README-Game.md", "README-Game.md", "pages/README-Game.md"],
    "archive":    [".github/pages/README-Archive.md", "README-Archive.md", "pages/README-Archive.md"],
}
STATUS = {":white_check_mark:": "已上线", ":clock8:": "开发中", ":x:": "已关闭"}


def kw_match(text, kw):
    """英文/数字关键词用词边界匹配（避免 AI 命中 AppImage），中文用子串"""
    t, k = text.lower(), kw.lower()
    if k.isascii() and k.isalnum():
        return re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", t) is not None
    return k in t


def get_mirrors():
    raw = os.environ.get("OPC_GH_MIRRORS", DEFAULT_MIRRORS)
    return [m.strip() for m in raw.split(",") if m.strip()]


def mirror_url(m, repo, path, branch):
    if m == "direct":
        return "https://raw.githubusercontent.com/%s/%s/%s" % (repo, branch, path)
    return m.replace("{repo}", repo).replace("{branch}", branch).replace("{path}", path)


def fetch_once(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "opc-track-lab/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def looks_valid(text):
    return len(text) >= 10 and "404: Not Found" not in text[:100] and "Couldn't find" not in text[:100]


def fetch_chain(repo, paths, branch="master", timeout=10):
    """按 镜像×路径 回退抓取，返回 (content, 说明) 或 (None, 错误列表)"""
    errs = []
    for m in get_mirrors():
        for p in paths:
            url = mirror_url(m, repo, p, branch)
            try:
                t0 = time.time()
                data = fetch_once(url, timeout)
                if looks_valid(data):
                    return data, "%s/%s via %s (%.1fs)" % (repo, p, m, time.time() - t0)
                errs.append("%s %s -> 无效内容 %dB" % (m, p, len(data)))
            except Exception as e:
                errs.append("%s %s -> %s" % (m, p, type(e).__name__))
    return None, errs


# ---------- 缓存 ----------

def cache_dir(explicit=None):
    d = explicit or os.path.join(os.getcwd(), "opc-doc", "case-cache")
    os.makedirs(d, exist_ok=True)
    return d


def load_meta(cdir):
    p = os.path.join(cdir, "meta.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_meta(cdir, meta):
    with open(os.path.join(cdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def cache_age_days(date_str):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(date_str)).days
    except Exception:
        return 999


def fetch_or_cache(name, paths, repo, cdir, force, branch="master"):
    """返回 (content, 提示信息)；优先用 7 天内缓存"""
    meta = load_meta(cdir)
    ent = meta.get(name)
    if ent and not force:
        fp = os.path.join(cdir, ent["file"])
        if os.path.exists(fp):
            age = cache_age_days(ent["date"])
            with open(fp, encoding="utf-8") as f:
                data = f.read()
            note = "缓存 %s（%d 天前，经 %s）" % (ent["date"], age, ent.get("mirror", "?"))
            if age >= 7:
                note += " — 已超 7 天，建议 --force 刷新"
            return data, note
    data, info = fetch_chain(repo, paths, branch)
    if data is None:
        return None, "抓取失败: " + "; ".join(info[:6])
    date = datetime.date.today().isoformat()
    fname = "%s-%s.md" % (name, date.replace("-", ""))
    with open(os.path.join(cdir, fname), "w", encoding="utf-8") as f:
        f.write(data)
    meta[name] = {"date": date, "file": fname, "mirror": info}
    save_meta(cdir, meta)
    return data, "新抓取 %s" % info


# ---------- 1c7 解析 ----------

ENTRY_RE = re.compile(r"^\*\s+(:[a-z_0-9]+:)\s+\[([^\]]+)\]\(([^)\s]+)\)[：:]\s*(.*)$")


def parse_entries(text):
    """返回 [(date_section, author, status, name, url, desc)]"""
    out, section, author = [], "", ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("### "):
            section, author = s[4:].strip(), ""
        elif s.startswith("#### "):
            author = re.sub(r"\s*-\s*\[Github\].*$", "", s[5:]).strip()
        else:
            m = ENTRY_RE.match(s)
            if m:
                status = STATUS.get(m.group(1), m.group(1))
                out.append((section, author, status, m.group(2), m.group(3), m.group(4)))
    return out


def cmd_cases(args):
    cdir = cache_dir(args.cache_dir)
    editions = list(EDITIONS) if args.edition == "all" else [args.edition]
    all_entries, notes = [], []
    for ed in editions:
        data, note = fetch_or_cache(ed, EDITIONS[ed], REPO_1C7, cdir, args.force)
        if data is None:
            notes.append("[%s] %s" % (ed, note))
            continue
        notes.append("[%s] %s，解析 %d 条" % (ed, note, len(parse_entries(data))))
        all_entries.extend(parse_entries(data))
    for n in notes:
        print(n)

    if args.stats:
        from collections import Counter
        c = Counter(e[2] for e in all_entries)
        dates = [e[0] for e in all_entries if re.match(r"\d{4}", e[0])]
        print("--- 统计 ---")
        print("条目总数: %d" % len(all_entries))
        for k in ("已上线", "开发中", "已关闭"):
            print("%s: %d" % (k, c.get(k, 0)))
        if dates:
            print("日期节范围: %s ~ %s（共 %s 节）" % (dates[-1], dates[0], len(set(dates))))
        return

    if not args.track:
        print("（未给 --track 关键词：已抓取并缓存。统计用 --stats，过滤用 --track）")
        return

    kw = args.track.lower()
    hits = [e for e in all_entries if kw_match(e[3] + " " + e[5], args.track)]
    print("--- 关键词「%s」命中 %d 条（显示前 %d）---" % (args.track, len(hits), args.limit))
    for sec, author, status, name, url, desc in hits[: args.limit]:
        print("[%s] %s — %s" % (status, name, desc[:120]))
        print("    作者: %s | 日期节: %s | %s" % (author or "?", sec or "?", url))
    if not hits:
        print("（案例库查无此关键词——若是域外领域请按 SKILL.md「域外赛道处理」，不要硬套）")


# ---------- Awesome ----------

AW_LINE_RE = re.compile(r"^-\s+\[([^\]]+)\]\(([^)\s]+)\)\s*-\s*(.*)$")


def parse_awesome(text):
    out, cat = [], ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            cat = s[3:].strip()
        else:
            m = AW_LINE_RE.match(s)
            if m:
                out.append((cat, m.group(1), m.group(2), m.group(3)))
    return out


def cmd_awesome(args):
    cdir = cache_dir(args.cache_dir)
    data, note = fetch_or_cache("awesome", ["readme.md", "README.md"], REPO_AWESOME, cdir, args.force)
    if data is None:
        print(note)
        return
    entries = parse_awesome(data)
    print(note + "，解析 %d 条子清单" % len(entries))
    if not args.keyword:
        from collections import Counter
        cnt = Counter(e[0] for e in entries)
        print("--- 方向地图：大类及子清单数 ---")
        for cat, n in cnt.most_common():
            print("%-24s %d" % (cat, n))
        return
    kw = args.keyword.lower()
    hits = [e for e in entries if kw_match(e[0] + " " + e[1] + " " + e[3], args.keyword)]
    print("--- 关键词「%s」命中 %d 条（显示前 %d）---" % (args.keyword, len(hits), args.limit))
    for cat, name, url, desc in hits[: args.limit]:
        print("[%s] %s — %s" % (cat, name, desc[:100]))
        print("    %s" % url)


# ---------- raw / check / update-self ----------

def cmd_raw(args):
    parts = args.repo_path.split("/", 2)
    if len(parts) != 3:
        print("用法: raw OWNER/REPO/路径")
        return
    repo, path = parts[0] + "/" + parts[1], parts[2]
    branches = [args.branch] if args.branch else ["master", "main"]
    data, info = None, []
    for br in branches:
        data, info = fetch_chain(repo, [path], branch=br)
        if data:
            break
    if data is None:
        print("抓取失败: " + "; ".join(info[:6]))
        return
    if args.save:
        fp = os.path.join(cache_dir(args.cache_dir), args.save)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(data)
        print("已保存: %s（%d 字符，来源: %s）" % (fp, len(data), info))
    else:
        print(data)


def cmd_check(_):
    print("镜像探测（探针: %s/%s）" % (PROBE_REPO, PROBE_PATH))
    ok = 0
    for m in get_mirrors():
        url = mirror_url(m, PROBE_REPO, PROBE_PATH, "master")
        t0 = time.time()
        try:
            data = fetch_once(url, timeout=8)
            good = looks_valid(data)
            ok += 1 if good else 0
            print("%-72s %s (%.1fs)" % (m[:70], "OK" if good else "内容无效", time.time() - t0))
        except Exception as e:
            print("%-72s FAIL %s" % (m[:70], type(e).__name__))
    print("可用: %d/%d" % (ok, len(get_mirrors())))


def cmd_update_self():
    repo = os.environ.get("OPC_SKILL_REPO", "")
    if not repo:
        print("未设置 OPC_SKILL_REPO（格式 owner/repo），跳过自更新。")
        print("发布技能后: set OPC_SKILL_REPO=你的用户名/opc-track-lab 再运行 --update-self")
        return
    branch = os.environ.get("OPC_SKILL_BRANCH", "master")
    base = os.path.dirname(SKILL_DIR)
    files = ["SKILL.md", "scripts/gh-fetch.py"] + [
        "references/" + f for f in sorted(os.listdir(os.path.join(SKILL_DIR, "references")))
    ]
    ok = 0
    for rel in files:
        data, info = fetch_chain(repo, [rel], branch=branch)
        dest = os.path.join(base, "opc-track-lab", rel) if os.path.basename(SKILL_DIR) != "opc-track-lab" else os.path.join(SKILL_DIR, rel)
        if data is None:
            print("FAIL %s: %s" % (rel, "; ".join(info[:2])))
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(data)
        ok += 1
        print("OK   %s <- %s" % (rel, info))
    print("自更新完成: %d/%d" % (ok, len(files)))


def main():
    ap = argparse.ArgumentParser(description="opc-track-lab 案例活取器")
    ap.add_argument("--update-self", action="store_true", help="从 OPC_SKILL_REPO 更新技能自身")
    sub = ap.add_subparsers(dest="cmd")
    pc = sub.add_parser("cases", help="抓/读 1c7 案例列表")
    pc.add_argument("--edition", default="main", choices=list(EDITIONS) + ["all"])
    pc.add_argument("--track", default="", help="关键词过滤（项目名+介绍）")
    pc.add_argument("--stats", action="store_true")
    pc.add_argument("--force", action="store_true")
    pc.add_argument("--limit", type=int, default=60)
    pc.add_argument("--cache-dir", default=None)
    pa = sub.add_parser("awesome", help="Awesome 方向地图")
    pa.add_argument("keyword", nargs="?", default="")
    pa.add_argument("--force", action="store_true")
    pa.add_argument("--limit", type=int, default=80)
    pa.add_argument("--cache-dir", default=None)
    pr = sub.add_parser("raw", help="抓任意仓库文件")
    pr.add_argument("repo_path", help="OWNER/REPO/路径")
    pr.add_argument("--branch", default=None, help="默认依次试 master/main")
    pr.add_argument("--save", default=None)
    pr.add_argument("--cache-dir", default=None)
    pchk = sub.add_parser("check", help="探测镜像存活")
    args = ap.parse_args()
    if args.update_self:
        cmd_update_self()
    elif args.cmd == "cases":
        cmd_cases(args)
    elif args.cmd == "awesome":
        cmd_awesome(args)
    elif args.cmd == "raw":
        cmd_raw(args)
    elif args.cmd == "check":
        cmd_check(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
