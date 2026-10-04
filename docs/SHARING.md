# Share a reproducible research card

```shell
python -m bshl share --card outputs/three-cases/no-stop/card.json --output outputs/no-stop.svg
```

The SVG contains no scripts, external fonts or remote images. It preserves analysis ID, decision time, rule version, data label, current state, source and selected-stop/kill-switch invalidation. Personal account sizing and outcome notes are omitted. Check the source URL before sharing; it can identify a private dataset. The full JSON remains the reproducibility record.

![Synthetic card](../examples/current/no-stop/share.svg)

## Repository cover and Topics

[Social Preview PNG](../assets/social-preview.png): 1280×640, below 1 MB. Upload through repository Settings → General → Social preview. Its presence in Git alone does not set GitHub's repository cover. The optional `scripts/render_social_preview.py` renderer needs Pillow (`.[visual]`).

Topics: `agent-skills`, `investment-research`, `technical-analysis`, `risk-management`, `python`, `backtesting`, `explainable-ai`. Backtesting refers to the documented cash simulator, not verified profit.

README, reproducible demos and precise Topics improve understanding and topic discovery. They do not guarantee recommendation, Star growth or organic reach. Gather real failures and real user feedback before making adoption claims.
