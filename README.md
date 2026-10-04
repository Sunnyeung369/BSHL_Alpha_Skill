# BSHL Alpha Skill

**Evidence-first research and explainable trade readiness.**
证据驱动投研与交易准备：记录依据、识别风险、保存判断和复盘。

## Current status / 当前状态

The six-batch upgrade is in progress. The legacy prototype did not establish a trading edge. Mock data is not live market data. No broker or order execution is included.

六批升级正在推进。旧原型未证明交易优势；模拟数据不能作为真实行情。所有规则阈值都需要独立验证。

| Capability | Status |
|---|---|
| Evidence and contradiction workflows | Available as research instructions |
| Strict scoring and risk gates | Regression tested; unknowns cannot pass |
| CSV daily structure and research cards | Offline CLI, source/time checks and schema tests |
| Event replay and watchlists | Follow the [roadmap](VERSION_ROADMAP.md) |
| Legacy Yahoo/SEC/Crypto/news adapters | Placeholders; real calls must fail explicitly |
| Autonomous orders | Not included |

## Start here

- [Quickstart](QUICKSTART.md): environment, skill loading and verification.
- [Skill entrypoint](SKILL.md): workflows and evidence rules.
- [Implementation roadmap](VERSION_ROADMAP.md): six batches and acceptance.
- [Contribute](CONTRIBUTING.md): reproducible failures and data adapters.
- [Security](SECURITY.md): credentials and private decision records.

The original six-layer architecture is retained as [historical design](docs/archive/v0.5-design.md). Its completion claims and examples have not all been validated.

## Verify locally

```shell
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

Python 3.10+; Windows additionally installs `tzdata` for IANA timezones. CI installs the optional JSON Schema validator. Windows, Linux and macOS jobs are configured; their live results determine verification status. Install the environment before running the checks.

MIT license. Research assistance and reproducibility are the purpose; results are not profitability guarantees.
