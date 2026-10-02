# 阶段 4 · 商业模式设计

> 蒸馏自 easychen/opc-methodology 官方技能 `opc-business-model-design`（SKILL.md + lean-canvas-lite、bmc-lite、pricing-checklist），中文改写版（2026-10）。冲突时以官方为准。

## 目标

把"这个生意如何成立"拆清楚，**而不是直接替用户填完一张画布**。防止商模没想清楚就盲目做产品。

## 边界

**不做**：MVP 设计/产品原型、获客流程/内容计划、运营 SOP——出现即拉回："这属于后续 MVP 或执行阶段的范围。我们先把商业模式的假设确认清楚，再推进。"

## 框架：Lean Canvas 九模块（按此顺序逐个确认，一次一个模块）

1. **Problem** — 这类用户最核心的问题（对应阶段 2/3 的结论）
2. **Customer Segments** — 目标客群
3. **Unique Value Proposition** — 独特价值主张（来自阶段 3）
4. **Solution** — 你打算怎么解决（先卖什么）
5. **Channels** — 用户通过什么渠道找到你（路径级别，不做获客执行）
6. **Revenue Streams** — 更想怎么收费
7. **Cost Structure** — 成本结构
8. **Key Metrics** — 关键指标（哪个数字能说明生意成立）
9. **Unfair Advantage** — 别人拿不走的优势（来自资源盘点）

关键模块（定价方式/渠道路径/收入结构）给 3 个候选 + "4. 我有自己的方案"，说明各自适用情况、优点、代价。

## 校验 1：BMC Lite（九项过一遍）

价值主张 / 客户细分 / 渠道 / 客户关系 / 收入来源 / 核心活动 / 核心资源 / 关键合作 / 成本结构——填完 Lean Canvas 后轻量过一遍，找漏项和矛盾。

## 校验 2：定价检查清单

1. 用户是否为**结果**付费，而不是为信息付费
2. 客单价是否覆盖交付复杂度
3. 是否有低摩擦入口产品
4. 是否有后续升级空间
5. 是否适合一人公司承接

## 收尾：提炼高风险假设

从九模块里找出"如果它是错的、整个生意就不成立"的假设（一般 1~3 条），写清单——它们是阶段 5 MVP 的验证对象。收入方式和价值主张冲突时，指出冲突并给备选，不直接定案。

## 落盘检查点（用户确认后立即执行）

1. `opc-doc/outputs/04-business-model/lean-canvas.md` — 九模块填写结果
2. `opc-doc/outputs/04-business-model/business-model-canvas-lite.md` — BMC Lite 校验结论
3. `opc-doc/outputs/04-business-model/pricing-notes.md` — 收费方式假设
4. `opc-doc/outputs/04-business-model/risky-assumptions.md` — 高风险假设清单（供 MVP 优先验证）
5. `opc-doc/state/current-stage.json` → `{"stage":"04-business-model","status":"completed","next_stage":"06-mvp-designer","summary":"一句话商模核心"}`；`decisions.json` 追加商模决策；`assumptions.json` 写入高风险假设列表

落盘后告知："✅ 商业模式结论已保存。下次对话可以从 MVP 设计继续。"

## 完成标准

- [ ] Lean Canvas 九模块完成
- [ ] 高风险假设已提炼
- [ ] 用户确认商模方向
- [ ] 已落盘
