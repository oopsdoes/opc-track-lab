# opc-track-lab · 一人企业赛道推演实验室

一个装进 AI 编程工具的技能（Skill）：以引导式对话带你完成一人企业的**赛道推演与建盘**（六阶段）、**拆解任意项目**、**出海快速闭环**。方法蒸馏自 easychen《一人企业方法论》第二版及其官方 9 个 Agent 技能；案例数据不捆绑、用时分批从公开仓库现抓；内置 **Jev 判断关**——关键判断由"AI 出题 → 判卷模型裸判 → 双列对照 → 用户终判"四步完成，防编造、防拍脑袋。

兼容 ZCode / Codex / Claude Code / DSH 等支持 Agent Skills（SKILL.md）的工具。

## 安装

将整个 `opc-track-lab/` 文件夹放入工具的技能目录（如 `~/.agents/skills/`），重启工具即可。三种获取方式：

```bash
# 路线 1：git 直连（能访问 GitHub 的环境）
git clone https://github.com/<你的用户名>/opc-track-lab.git

# 路线 2：镜像代理（国内推荐）
git clone https://gh-proxy.com/https://github.com/<你的用户名>/opc-track-lab.git

# 路线 3：jsDelivr 逐文件（无 git 环境时）
# 浏览器打开 https://cdn.jsdelivr.net/gh/<用户名>/opc-track-lab@master/ 按目录逐个另存
```

## Jev 判断关：判卷模型配置（三插口 + 通配口）

判断关支持**三个原生插口 + 一个通配口**，配置三个环境变量即可，未配置时自动降级「单阅卷」（AI 自判并在卡片标注），**流程永不阻塞**。

> 说明：亲测路线是**插口 A（OpenRouter）**——注册有送额度活动、国内配置成本最低；插口 B（TypeSafe 官方）、插口 C（硅基流动）与通配口均已适配协议但未逐一实测。如果发现了更好的判卷渠道（更便宜、更快、更稳，或本地 Laya 跑通了），**欢迎提 Issue 或 PR** 分享配置，我会把它加进这份说明里。

### 插口 A · OpenRouter（推荐，本仓库实测路线）

OpenRouter 聚合了 Jev（typesafe/jev-1.13），**注册送 5 美元额度**（约 1.2 亿 token，每次判卷不到一分钱，够用很久）。

1. 注册 [openrouter.ai](https://openrouter.ai)（有送额度活动，以官网为准）
2. 在 [Keys 页](https://openrouter.ai/keys) 创建 API Key
3. Windows 下（`setx` 为用户级持久变量；macOS/Linux 写入 shell 配置）：

```bat
setx OPC_JUDGE_BASE_URL "https://openrouter.ai/api/v1"
setx OPC_JUDGE_API_KEY "sk-or-v1-你的key"
setx OPC_JUDGE_MODEL "typesafe/jev-1.13"
```

安全须知：Key 只放环境变量，**不要提交进仓库、不要写进技能文件**；本 README 与脚本中不含任何 Key。Key 泄露时去 Keys 页随时撤销重发。

### 插口 B · Jev 官方直连（TypeSafe AI）

不走 OpenRouter，直接用 TypeSafe 官方 API：

1. 访问 [typesafe.ai](https://typesafe.ai) 注册账号，在 Dashboard 创建 API Key（分步教程见 [Apidog 教程](https://apidog.com/blog/jev-api-key)）
2. 官方接口为 `https://api.typesafe.ai` 的决策端点（`/v1/decide`，发送 state+questions、返回带校准概率的 answers，详见[官方文档](https://docs.typesafe.ai/api)与[快速上手](https://docs.typesafe.ai/introduction/quickstart)）：

```bat
setx OPC_JUDGE_BASE_URL "https://api.typesafe.ai"
setx OPC_JUDGE_API_KEY "你在 dashboard 拿到的 key"
setx OPC_JUDGE_MODEL "按官方文档填模型名"
```

> 注：本仓库实测验证的是插口 A；插口 B 的端点与响应以 [docs.typesafe.ai](https://docs.typesafe.ai/api) 为准，如字段有出入可用 `OPC_JUDGE_DECISIONS_PATH` 覆盖路径，或提 Issue 反馈。

### 插口 C · 硅基流动（国内直连，未实测）

国内注册不了 OpenRouter、连不上 TypeSafe 官方时的**替代路线**：硅基流动 2026 年 9 月底上线了「快速决策（TypeSafe）」接口（`POST /v1/systemone`），与 Jev 同一套 state+questions 协议，目前挂了三个开源判断模型：

| 模型 | 底细 |
| --- | --- |
| `Kev-4b` | 通义千问 Qwen3.5 微调的 Jev 复刻，API 规范全复现 |
| `SemIf` | 独立开源实现，社区 98 题实测 82%（Jev 本体同一测试 80%） |
| `diffusiongemma` | Gemma 系扩散架构改的判断模型，较新 |

活动（以[官方文档](https://docs.siliconflow.cn/docs/api/systemone-post)为准）：Alpha 阶段**输入 token 2026-10-08 前限时免费**，此后如收费将另行通知；输出 token 目前不计费。

1. 注册 [cloud.siliconflow.cn](https://cloud.siliconflow.cn)，在「API 密钥」页新建 Key
2. 三个变量照旧（脚本已预留硅基流动端点，`OPC_JUDGE_BASE_URL` 指向即自动走 `/v1/systemone`）：

```bat
setx OPC_JUDGE_BASE_URL "https://api.siliconflow.cn"
setx OPC_JUDGE_API_KEY "sk-你在硅基流动的key"
setx OPC_JUDGE_MODEL "Kev-4b"
```

> **诚实声明：本仓库实测过的只有插口 A。** 插口 C 与 Jev 同协议、脚本已预留接口，但**没有实测过**——响应字段如与 Jev 有出入，可用 `OPC_JUDGE_DECISIONS_PATH` 覆盖或提 Issue。模型名大小写以官方文档为准；想在硅基流动改用普通对话模型当判卷员，加 `setx OPC_JUDGE_API "chat"` 强制 chat 协议即可。另外注意：硅基流动模型广场的筛选面板里没有「判断」分类，这三个模型的入口就是上面的 API 文档页。

### 通配口 · 其他 OpenAI 兼容接口（chat 协议）

千问 DashScope / 豆包火山方舟 / 智谱 / 本地 Laya 网关等，同样三个变量，脚本自动切 chat 协议（严格系统提示+温度 0 模拟判卷纪律）：

```bat
setx OPC_JUDGE_BASE_URL "https://dashscope.aliyuncs.com/compatible-mode/v1"
setx OPC_JUDGE_API_KEY "sk-xxx"
setx OPC_JUDGE_MODEL "qwen-flash"
```

### 判断关怎么工作（给读者的一句话版）

推演到关键判断（四问快筛、六维评分、MVP 到期验收、复盘诊断）时：AI 从你的推演档案组装"考卷"（材料+题目）→ 判卷模型只返回裸分数/选项（不写一个字，没法编理由）→ AI 把**双方分数并排**给你看，分歧处高亮 → **你终判**。出题的是 AI，阅卷的是判卷模型，拍板的是你。

## 案例活取（中国独立开发者列表 + Awesome 方向地图）

案例不打包进技能（防过时），用时现抓，缓存 7 天：

```bash
python scripts/gh-fetch.py check                      # 测哪个镜像活着
python scripts/gh-fetch.py cases --track 翻译          # 1c7 列表按关键词过滤
python scripts/gh-fetch.py cases --stats               # 规模统计
python scripts/gh-fetch.py awesome AI                  # Awesome 方向地图
python scripts/gh-fetch.py raw owner/repo/path.md      # 抓任意公开仓库文件
```

内置四级镜像回退（直连 → jsDelivr 三域 → gh-proxy → 手动指引），国内无代理环境可用。抓不到时用旧缓存或无案例推演，不阻塞。

## 使用

对装了本技能的 AI 说：**"开始赛道推演"**（六阶段建盘）／**"帮我拆个项目"** ／**"出海闭环"** ／**"继续推演"**（断点续推）。推演进度与判断记录落盘在工作目录 `opc-doc/`。

## 边界与声明

- 案例事实以抓取原文为准并注明日期；判卷模型返回裸结果，解释均标注「AI 解读」
- 案例库只覆盖网站/App/开源生态；线下赛道走"域外处理"（不硬套、反向访谈用户经验）
- 六维评分只作候选间相对参考；所有产出需用户确认后落盘
- V2 计划：批量案例匹配（判卷模型逐条扫全库找同类）、全网案例源、月报复盘接入

## 来源与致谢

- 方法论：easychen《一人企业方法论》第二版（[easychen/opc-methodology](https://github.com/easychen/opc-methodology)）及其官方 9 技能，本技能为中文蒸馏改写，冲突以官方为准
- 案例库：[1c7/chinese-independent-developer](https://github.com/1c7/chinese-independent-developer)、[sindresorhus/awesome](https://github.com/sindresorhus/awesome)
- 判断关灵感：TypeSafe AI 的 Jev（System One 判断模型）与开源 Laya
