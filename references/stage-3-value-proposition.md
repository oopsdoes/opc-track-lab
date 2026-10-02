# 阶段 3 · 价值主张

> 蒸馏自 easychen/opc-methodology 官方技能 `opc-value-proposition`（SKILL.md + vpc-lite、messaging-template），中文改写版（2026-10）。冲突时以官方为准。

## 目标

明确"这类人为什么要买你"，给出可选择的价值主张方案。**只做"为什么买你"的结构化分析，不进入话术设计或内容创作。**

## 边界

**不做**：广告文案/推广话术、内容选题、定价策略、转化路径——出现即记录并拉回："这些执行细节很重要，我们会在后续阶段专门处理。现在先把'为什么买你'的逻辑框架确认好。"

## 框架：价值主张画布（简版）

**客户侧**（先问）：
- **Jobs**：用户正在完成什么任务（想完成什么）
- **Pains**：完成任务时最痛的阻碍、风险或成本
- **Gains**：理想中想得到的收益

**产品侧**（后对）：
- **Products / Services**：你提供什么
- **Pain Relievers**：如何降低痛苦
- **Gain Creators**：如何放大收益

一类细分客户对应一类价值主张。

## 执行步骤

1. 读前置：`opc-doc/outputs/02-niche-positioning/target-segment.json` + `positioning-statement.md`（缺失则先回阶段 2）
2. 一次一问推进（轻且相关可合并 2~3 问）：最想得到的结果？最痛的一点？为什么不满意现有方案？
3. 每轮用白话总结当前 jobs/pains/gains 理解
4. 生成 **3 个价值主张版本**（典型如：**提效型** / **结果型** / **降风险型**），每个说明适用情况、优点、代价 + "4. 我有自己的方案"
5. 用户选择/组合/修改 → 确认后落盘

多个版本都可行时**并列呈现，不替用户拍板**；用户对术语不熟就用更白话的表达。

## 表述层产出（框架层，非广告话术）

至少三种说法：
1. 一句话版本
2. 面向用户的短说明
3. 用于内容或落地页的主标题草案

要求：不抽象空泛、直接说用户得到什么、体现与替代方案的差异。

## 落盘检查点（用户确认后立即执行）

1. `opc-doc/outputs/03-value-proposition/value-proposition-canvas.md` — Jobs/Pains/Gains + Pain Relievers/Gain Creators 完整画布
2. `opc-doc/outputs/03-value-proposition/segment-vp-matrix.md` — 目标客群 × 价值主张对应关系
3. `opc-doc/outputs/03-value-proposition/messaging.md` — 确认的主价值主张表述（三种说法）
4. `opc-doc/state/current-stage.json` → `{"stage":"03-value-proposition","status":"completed","next_stage":"04-business-model","summary":"一句话价值主张核心"}`；`decisions.json` 追加确认版本

落盘后告知："✅ 价值主张结论已保存。下次对话可以从商业模式设计继续。"

## 完成标准

- [ ] 画布关键模块完整（Jobs/Pains/Gains/Products/Pain Relievers/Gain Creators）
- [ ] 用户已确认主价值主张版本
- [ ] 已落盘
