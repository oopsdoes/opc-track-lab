#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev-check.py — Jev 判断关：把"考卷"交给判卷模型复判（双协议）

角色分工（铁律）：AI 出题（组装 state+questions，材料全部来自 opc-doc 现有产物）
→ 判卷模型只判不写（返回裸分数/选项/概率，无解释）→ AI 对答案、向用户呈现双列对照。

支持两类判卷模型（自动识别，也可用 OPC_JUDGE_API=decisions|chat 强制指定）：
  1. decisions 协议 — 判断型模型原生接口：
     a. OpenRouter 上的 Jev（typesafe/jev-*，推荐，注册有额度）：
        POST {root}/api/alpha/decisions
     b. TypeSafe 官方直连（https://api.typesafe.ai）：
        POST {base}/v1/decide
     c. 硅基流动（https://api.siliconflow.cn，Kev-4b/SemIf/diffusiongemma，未实测）：
        POST {base}/v1/systemone
     body={model, state, questions{...}}，返回 noul(是/否概率)/choice(选项+分布)/score(量表位置+分布)
  2. chat 协议 — 其他 OpenAI 兼容接口（千问 DashScope/豆包方舟/智谱/本地 Laya 网关等）：
     POST {base}/chat/completions，用严格系统提示模拟判卷纪律（温度 0、只答题号和答案）
  决策端点路径可用 OPC_JUDGE_DECISIONS_PATH 覆盖（默认按 base 自动识别）。

考卷格式（JSON 文件，由 AI 在会话中生成）：
{
  "title": "候选赛道六维评分复判",
  "state": "判题所需事实（精简，缺材料先标待补）",
  "questions": [
    {"id": "niche-ok", "type": "noul",  "ask": "是否为小众刚需？",
     "criteria_true": "大众弱需求但该人群强需求", "criteria_false": "大众刚需红海"},
    {"id": "best",     "type": "choice", "options": ["A", "B", "C"], "ask": "资源匹配最高的是？"},
    {"id": "A-pain",   "type": "score",  "scale": [1, 5], "ask": "候选赛道A痛点强度"}
  ]
}

判卷模型配置（环境变量）：
  OPC_JUDGE_BASE_URL   例 https://openrouter.ai/api/v1
                       或 https://dashscope.aliyuncs.com/compatible-mode/v1（千问）
                       或 https://open.bigmodel.cn/api/paas/v4（智谱）/ 火山方舟 / 本地 Laya 网关
  OPC_JUDGE_API_KEY
  OPC_JUDGE_MODEL      typesafe/jev-1.13 或其他模型 ID
未配置时不报错：提示本次为"单阅卷"（AI 自判并标注），流程永不阻塞。

用法：python jev-check.py 考卷.json [--out 结果.json] [--timeout 60]
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SYS_PROMPT = (
    "你是判卷模型。你只能依据给出的材料作答，材料之外的知识一律不使用。"
    "对每道题只输出一行：题号. 答案。分数题答数字，选择题答选项字母或选项文字，"
    "是否题答“是”或“否”。禁止任何解释、分析、理由或多余文字。"
)


def check_config():
    base = os.environ.get("OPC_JUDGE_BASE_URL", "").strip().rstrip("/")
    key = os.environ.get("OPC_JUDGE_API_KEY", "").strip()
    model = os.environ.get("OPC_JUDGE_MODEL", "").strip()
    return base, key, model


def detect_api(base, model):
    forced = os.environ.get("OPC_JUDGE_API", "").strip().lower()
    if forced in ("decisions", "chat"):
        return forced
    m = (model or "").lower()
    if "openrouter" in base and ("jev" in m or "typesafe" in m):
        return "decisions"
    if "siliconflow" in base:
        return "decisions"
    return "chat"


def post_json(url, payload, key, timeout):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + key,
        "User-Agent": "opc-track-lab/jev-check"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


# ---------- decisions 协议（Jev 原生） ----------

def to_decisions_questions(questions):
    qs = {}
    for q in questions:
        qid, ask = q.get("id"), q.get("ask", "")
        t = q.get("type")
        if t == "noul":
            qs[qid] = {"type": "noul", "instructions": ask, "criteria": {
                "true": q.get("criteria_true", "是"), "false": q.get("criteria_false", "否")}}
        elif t == "choice":
            crit = q.get("criteria") or {o: o for o in q.get("options", [])}
            qs[qid] = {"type": "choice", "instructions": ask, "criteria": crit}
        else:  # score
            scale = q.get("scale", [1, 5])
            labels = q.get("criteria") or ["%s 分" % n for n in range(scale[0], scale[-1] + 1)]
            qs[qid] = {"type": "score", "instructions": ask, "criteria": labels}
    return qs


def decisions_url(base):
    override = os.environ.get("OPC_JUDGE_DECISIONS_PATH", "").strip()
    if override:
        return base.rstrip("/") + "/" + override.lstrip("/")
    b = base.rstrip("/")
    if "openrouter" in b:
        if b.endswith("/api/v1"):
            return b[: -len("/api/v1")] + "/api/alpha/decisions"
        return b + "/api/alpha/decisions"
    if "siliconflow" in b:
        if b.endswith("/v1"):
            b = b[: -len("/v1")]
        return b + "/v1/systemone"  # 硅基流动「快速决策（TypeSafe）」端点（未实测）
    if "typesafe.ai" in b:
        return b + "/v1/decide"  # TypeSafe 官方直连（以 docs.typesafe.ai 为准）
    return b + "/api/alpha/decisions"


def call_decisions(base, key, model, exam, timeout):
    payload = {"model": model, "state": exam.get("state", ""),
               "questions": to_decisions_questions(exam.get("questions", []))}
    return post_json(decisions_url(base), payload, key, timeout)


def read_decisions_answers(data, questions):
    answers = data.get("answers", data) or {}
    results = []
    for q in questions:
        qid, t = q.get("id"), q.get("type")
        a = answers.get(qid, {}) or {}
        val, ok, note = "-", False, "未返回"
        if t == "noul":
            p = a.get("noul", a.get("probability"))
            if isinstance(p, (int, float)) and 0 <= p <= 1:
                val, ok = "%.2f（%s）" % (p, "是" if p > 0.5 else "否"), True
                note = "有效"
        elif t == "choice":
            c = a.get("choice")
            if c is not None:
                val, ok = str(c), str(c) in [str(o) for o in q.get("options", [])]
                note = "有效" if ok else "不在选项内"
        else:  # score
            s = a.get("score")
            if isinstance(s, (int, float)):
                scale = q.get("scale", [1, 5])
                n = len(q.get("criteria") or range(scale[0], scale[-1] + 1))
                lo, hi = (0, n - 1) if scale[0] == 0 or s == 0 else (1, n)
                val, ok = str(s), (lo <= s <= hi) if n else False
                note = "有效" if ok else "量表位置越界"
        results.append({"id": qid, "ask": q.get("ask", ""), "jev": val, "valid": ok, "note": note})
    return results


# ---------- chat 协议（OpenAI 兼容） ----------

def render_exam(exam):
    lines = ["【材料】", exam.get("state", "").strip() or "（无材料——此时不应出题）", "", "【题目】"]
    lines.append("（每题只答：题号. 答案）")
    for i, q in enumerate(exam.get("questions", []), 1):
        t = q.get("type")
        if t == "score":
            scale = q.get("scale", [1, 5])
            tag = "[%d-%d分]" % (scale[0], scale[-1])
        elif t == "noul":
            tag = "[是/否]"
        else:
            tag = "[%s]" % "/".join(q.get("options", []))
        lines.append("%d. %s: %s %s" % (i, q.get("id", "q%d" % i), q.get("ask", ""), tag))
    return "\n".join(lines)


def call_chat(base, key, model, exam_text, timeout):
    payload = {"model": model, "temperature": 0, "messages": [
        {"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": exam_text}]}
    data = post_json(base + "/chat/completions", payload, key, timeout)
    return data["choices"][0]["message"]["content"]


def parse_chat_answers(raw, questions):
    lookup = {}
    for line in raw.splitlines():
        m = re.match(r"^\s*(\d+)\s*[.、:：]?\s*(.+?)\s*$", line.strip())
        if m:
            lookup[int(m.group(1))] = m.group(2).strip().strip("。．.")
    results = []
    for i, q in enumerate(questions, 1):
        qid, a = q.get("id", "q%d" % i), lookup.get(i, "")
        ok, note = False, ""
        if not a:
            note = "未作答"
        elif q.get("type") == "score":
            scale = q.get("scale", [1, 5])
            num = re.search(r"-?\d+(\.\d+)?", a)
            if num and scale[0] <= float(num.group()) <= scale[-1]:
                a, ok, note = str(int(float(num.group()))), True, "有效"
            else:
                note = "超出范围或非数字"
        elif q.get("type") == "noul":
            if a.startswith("是"):
                a, ok, note = "是", True, "有效"
            elif a.startswith("否"):
                a, ok, note = "否", True, "有效"
            else:
                note = "非是/否"
        else:
            opts = [str(o).strip().upper() for o in q.get("options", [])]
            if a.upper() in opts:
                a, ok, note = a.upper(), True, "有效"
            else:
                note = "不在选项内"
        results.append({"id": qid, "ask": q.get("ask", ""), "jev": a if a else "-", "valid": ok, "note": note})
    return results


# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser(description="Jev 判断关：判卷模型复判")
    ap.add_argument("exam", help="考卷 JSON 文件路径")
    ap.add_argument("--out", default=None, help="结果 JSON 输出路径（默认与考卷同目录）")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    base, key, model = check_config()
    if not (base and key and model):
        print("〔单阅卷模式〕未配置判卷模型（OPC_JUDGE_BASE_URL / OPC_JUDGE_API_KEY / OPC_JUDGE_MODEL）。")
        print("本次判断由 AI 单独完成，判断卡片标注「单阅卷」；流程继续，不受阻塞。")
        print("配置任意 OpenAI 兼容接口（千问/豆包/智谱）、硅基流动或 OpenRouter-Jev 后自动升级为双阅卷。")
        return

    with open(args.exam, encoding="utf-8") as f:
        exam = json.load(f)
    questions = exam.get("questions", [])
    if not questions:
        print("考卷里没有题目。")
        return

    api = detect_api(base, model)
    print("〔双阅卷模式〕判卷模型: %s @ %s（%s 协议），共 %d 题" % (model, base, api, len(questions)))
    try:
        if api == "decisions":
            data = call_decisions(base, key, model, exam, args.timeout)
            results = read_decisions_answers(data, questions)
            raw = json.dumps(data.get("answers", data), ensure_ascii=False)
        else:
            raw = call_chat(base, key, model, render_exam(exam), args.timeout)
            results = parse_chat_answers(raw, questions)
    except urllib.error.HTTPError as e:
        print("判卷模型调用失败: HTTP %d %s — 按「单阅卷」继续，本节点标注「复判失败」。"
              % (e.code, e.read().decode("utf-8", "replace")[:160]))
        return
    except Exception as e:
        print("判卷模型调用失败: %s — 按「单阅卷」继续，本节点标注「复判失败」。" % type(e).__name__)
        return

    print("%-14s %-40s %-16s %s" % ("题号", "题目", "Jev判定", "校验"))
    print("-" * 84)
    for r in results:
        print("%-14s %-40s %-16s %s" % (r["id"], r["ask"][:38], str(r["jev"]), r["note"] if not r["valid"] else "OK"))

    out = args.out or (os.path.splitext(args.exam)[0] + ".result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"judge": model, "api": api,
                   "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                   "results": results, "raw": raw}, f, ensure_ascii=False, indent=2)
    print("结果已存: %s（AI 对答案后以双列判断卡片呈现给用户）" % out)


if __name__ == "__main__":
    main()


