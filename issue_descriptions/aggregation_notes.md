# 汇总说明

本次由新启动的汇总代理，在 72 份逐份目录冻结后分类。分类仅用于检索与关联，未重新审计原 rollout，未实施建议，未设置优先级，未删减、合并原条目或改写其判断。

阅读范围：
- README.md；manifest.json 的全部 72 条会话记录；per_report_validation.json 的覆盖及一致性信息。
- grouping_digest.jsonl 的全部 607 条完整 description 与 possible_solutions，连续批次为 1–40、41–120、121–200、201–280、281–360、361–440、441–520、521–607，均有完整工具返回。
- 另解析 all_items.json，逐项比对全部 digest 描述/方案与原文一致、index 为 1–607，使用原始 ID 和原文生成产物；按需要检查首条完整结构和现成渲染器。
- 未读取旧 report.md 或三个旧 summary.md，未扩读原 rollout。

完整性：
- manifest 为 72 份，包含 3 份 finding_count=0 会话：确认连接成功、检查 Chrome DevTools 工具（01a1570b-5750-7042-ae3e-e94b67aad107）、回应问候。这些会话的证据缺口/正例仍保留。
- 原台账元素覆盖 382/382；既有逐份校验无错误。
- 607 条全部保留：confirmed_issue 285、candidate_issue 46、evidence_gap 142、positive_context 134。
- 采用 120 个具体检索主题，每个原始 ID 仅有一个主组；组序不是重要性排序。正例按主题保留，没有从目录剔除。

关联边界：
- 同一父任务/子审、同一四 CLI 批次、同一包装器故障或相同 commit 回传可提供重复证据，不能按条目数解释成独立故障频率。
- 循环渲染、拒绝清草稿、保存竞态、旧报告字段、迁移键和混合快照存在父子对应；不同组件/触发条件仍不自动等于同一根因。
- CLI 角色依据 cwd、时间、handoff、commit 或 clarification id 关联；不把独立 CLI 伪造成 thread_spawn，不把继承回放算新增执行。
- UUID 候选解释、保存/打开超时、开发/生产差异、401、模型来源/snapshot 和架构候选仍不提升确定性。原始分类原样保留。
- 密文派发、原生截断/损坏、子任务无回传、工具无返回、未独立看图、缺原失败请求和未知等待分解，均尚不能确认。
- 仅讨论的 CFG 归属方案、未接入后端/AI、未启动 worker、未完成公网/上传等边界继续保留。用户新增规则或主动停止不追溯成早先违令。
- 并行墙钟、用户空档、授权等待、不同任务/服务器时间不直接求和。没有反事实基线，不给总节时、模型优劣或根因收益承诺。

产物：
- group_assignments.json：每个原始 ID 的唯一主组及跨组边界。
- all_issues.md：由 assemble_catalog.py render 从 all_items.json 原文生成，包含每条描述/方案/证据/判断边界/来源。
- aggregation_validation.json：成员全集、去重和原文渲染核验结果。

最终核验：
- render 返回 complete=true，source_items/assigned_items/unique_assigned_items 均为 607，missing_ids/extra_ids 均为空，groups=120。
- all_issues.md 逐个原 ID 恰有一个条目标题；全部原 description、possible_solutions、evidence 和 uncertainty 均存在于生成目录。
- 4 个冻结主输入、72 份逐份 JSON 和 72 份原审计 JSON 的 SHA256 均与核验依据一致；没有修改这些输入。