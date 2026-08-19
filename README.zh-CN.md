# Engineering Evidence Toolkit（工程证据工具箱）

这个仓库提供一组小而透明的工程证据治理 skill，用于把仿真、试验或解析结果整理成可追溯、可复核、可复现的证据链。v0.2 在兼容 v0.1 示例的同时，校验生命周期优先级、十六进制 SHA-256、唯一 ID、可解析声明引用和有效的帧/时间类型。它记录范围、来源、哈希、单位、坐标系、帧/时间、求解状态和声明就绪度，但不会把“求解器返回成功”夸大成“物理结论正确”。

仓库采用 Apache-2.0；示例全部为合成数据，不包含真实 ODB、CAE、论文、凭据或私人项目资料。

## 六个 skill

- [evidence-contract](skills/evidence-contract/SKILL.md)：先定义可检验的证据契约。
- [provenance-ledger](skills/provenance-ledger/SKILL.md)：维护输入、观测和变换的来源台账。
- [solver-status-gate](skills/solver-status-gate/SKILL.md)：区分 datacheck、求解完成、物理审查和发布就绪。
- [result-audit](skills/result-audit/SKILL.md)：检查符号、单位、坐标、帧、区域、基线和边界。
- [claim-readiness-audit](skills/claim-readiness-audit/SKILL.md)：把每条文字声明映射到可核验的证据。
- [reproducible-reporting](skills/reproducible-reporting/SKILL.md)：生成确定性的清单、环境记录和交接报告。

## 快速开始

```powershell
python -B scripts/evidence_check.py examples/synthetic/contract.json
python -B -m unittest discover -s tests -v
```

CLI 只做结构和证据链门禁，不替代求解器、ODB/结果审查或工程师签字。

## Abaqus 报告适配器

[`from_abaqus_audit.py`](scripts/from_abaqus_audit.py) 可读取 companion Abaqus 工作流输出的 `input_digest` + `findings` 报告，确定性地生成仅含静态审计的 0.2 契约；也可以用 `--model-input` 对模型输入文件计算摘要：

```powershell
python -B scripts/from_abaqus_audit.py examples/cross-repo/abaqus-agent-report.json contract.json
python -B scripts/evidence_check.py contract.json
```

公开的[跨仓库示例](examples/cross-repo/README.md)全部是合成数据。相同输入重复转换会产生完全相同的字节；checker 返回 `CONDITIONAL`，因为该示例没有声称求解器或物理审查已完成。

对 field/history 证据，`frame` 必须是非负整数，`time` 必须是有限且非负的数；static-audit/document 证据无需帧或时间。三个 solver 状态中任一失败即为 `BLOCKED`，否则任一待处理/必需状态为 `CONDITIONAL`。

详见英文 [README](README.md)、[架构说明](docs/architecture.md)、[快速开始](docs/quickstart.md) 和 [声明生命周期](docs/claim-lifecycle.md)。
