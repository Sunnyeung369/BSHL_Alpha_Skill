# Event simulation and its limits

```shell
python -m bshl backtest --csv bshl/assets/breakout.csv --metadata bshl/assets/breakout.metadata.json --train-end 2025-04-30 --test-start 2025-05-01 --output outputs/backtest.json
```

This is a daily US cash, long-only price strategy simulator. It does **not** backtest an Alpha thesis or infer historical fundamentals. The default signal is a close above the previous 20 highs with Wilder ATR14, stop distance 2 ATR and target 2R. These are experimental parameters. Reported results on bundled fixtures are fictional pipeline tests.

## Ordering and fills

Session opens, closes and data publication are distinct events. A signal uses only completed bars available by its decision time. It fills at the first session open strictly later than publication. Frozen stop/target levels are not moved using the next close. A gap outside those levels cancels entry. Sizing uses known decision-time volume, a 1% cash risk budget, a 10% cash allocation cap and whole shares. Defaults can be changed through `--config` JSON matching `BacktestConfig` fields.

Standing gap exits act at the next open. If a daily range touches both stop and target, stop wins conservatively. The simulator cannot reconstruct the intraday path. Slippage, half-spread and commission apply on both sides. It does not model market impact, partial fills, fees specific to venues, taxes, leverage, dividends or corporate actions. Use unadjusted prices over a corporate-action-free window.

## Evaluation

The report records parameters, source, trades, costs, equity, drawdown, average realized R and a buy-and-hold baseline using the same cost assumptions. That baseline allocates 100%, unlike the strategy cap; the difference is not matched-exposure alpha. An unfinished or unavailable final price stays unknown; an empty interval has no return claim.

It also records average winning/losing P&L after costs, realized win rate, failed trades, notional turnover/initial cash and wall-clock holding time (including overnight periods). Price position above/below MA20 is a simple diagnostic, not a calibrated market-regime classifier. Fewer than 30 closed trades are labelled insufficient; exceeding that count does not certify a strategy. If the last close was published late, the final position is marked at the known close without inventing a retroactive exit trade.

`train_end` must precede `test_start`. The two windows run with independent cash and fixed parameters. Earlier visible history may warm up the holdout, including a prior signal for its first eligible open. No optimizer or statistical edge certification is implemented. Fix the split and parameters before inspecting holdout results; the software cannot detect manual retuning. Custom Python callbacks receive immutable visible history but cannot be sandboxed against a future-data closure.

`performance_validated` always remains false. Real adoption requires independent, provenance-checked datasets, sample adequacy and sensitivity analysis. A successful unit test verifies mechanics, not profitable trading.
