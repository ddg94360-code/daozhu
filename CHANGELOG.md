# Changelog

All notable changes to 道樞 Dàoshū are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- 本機記憶儀表板（`python -m web`，`127.0.0.1:8765`）：週報／支出／健康／提醒／採買／情緒可寫入，筆記只讀
- `daily.check_shopping_by_id` / `daily.remove_shopping_by_id`（MCP：`daozhu_check_shopping_by_id` / `daozhu_remove_shopping_by_id`）
- `config.py` — optional `config.yaml` support (`timezone`, `currency`, `review_weekday`, `review_time`, `energy_analysis_days`, `high_speed_threshold`), with `config.yaml.example`
- `daozhu_export_expenses_csv` — export monthly expenses as CSV (auto-escapes commas)
- `daozhu_config_show` — inspect the active configuration
- Health log now returns `consecutive_days` (streak of days with sleep/exercise)
- Expense responses and weekly report now carry a `currency` symbol from config
- Weekly report reuses the already-fetched week's mood records for energy insight (one fewer file read)

### Tests
- Expanded 20 → 31: CONFIG loading (defaults / from YAML / unknown keys / missing file), CSV export, health streak, weekly currency field, solar-term across 2025–2027 and the cross-year boundary

### Docs
- English README (`README.md`) + Traditional Chinese (`README.zh-TW.md`) with language switcher
- `CONTRIBUTING.md`, `CHANGELOG.md`, `NOTICE`
- GitHub Actions CI (pytest across Python 3.10–3.13)
- Project badges (license, Python, CI)

## [1.0.0] — 2026-08-12

Initial open-source release.

### Added
- **Perception network** — 7 layers: emotion / task / interpersonal / complexity / concise-mode / tone / energy
- **Cabinet** — Confucian, Taoist, Legalist, Strategist schools + Military, Mohist, Buddhist patches
- **Skill modules** — Work Guide (百工鑑), Virtual Masters (百師錄), Music Companion (弦外之音), Metaphysical Mirror (萬象心鏡, 7 modes), Solar Terms (陰陽時令), Cabinet Meeting (內閣會議), Skill Routing
- **Memory layer MCP** — expense, health, reminders, shopping, mood journal, study notes, decision log, weekly report, energy insight, strategy vault (道藏), solar-term calendar
- Atomic JSON storage (`memory_store`) with corrupt-file backup, shared clock, subdir collections
- 31 tests across 4 suites
