# 道樞 Dàoshū — An Eastern-Philosophy AI Orchestrator

> **Languages:** [English](README.md) · [繁體中文](README.zh-TW.md)

**道樞 (Dàoshū, "Pivot of the Tao")** is a self-adaptive AI agent framework grounded in Eastern philosophy. A seven-layer perception network runs in the background to answer three questions about every input — *who are you, how are you, what do you need* — then decides which philosophical school should respond.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](mcp)
[![CI](https://github.com/ddg94360-code/daozhu/actions/workflows/test.yml/badge.svg)](https://github.com/ddg94360-code/daozhu/actions)

Feeling low? It answers as Taoism (道家). Stuck with a person? Confucianism (儒家). Negotiating? Strategic School (縱橫家). Torn between options? It convenes a cabinet meeting. Every reply is prefixed with `【感知：XXX】` (perception tag).

## Features

- **Seven-layer perception network** — emotion, task, interpersonal, complexity, concise-mode, tone, energy — fully automatic in the background
- **Cabinet of four schools** — Confucian (dual internal/external), Taoist (three-tier), Legalist (dual-domain / three-table), Strategist (opening-three-questions)
- **Three advisory patches** — Military (embedded in Strategist), Mohist logic (in Legalist), Buddhist insight (in Taoist)
- **Seven skill modules** — Work Guide, Virtual Masters, Music Companion, Metaphysical Mirror (hexagram/tarot/astrology/feng-shui/archetype/dream/oracle), Solar Terms, Cabinet Meeting, Skill Routing (hook in your own skills)
- **Memory layer MCP** — 23 tools: expense, health, reminders, shopping, mood journal, study notes, decision log, weekly report, energy insight, strategy vault (道藏), solar-term calendar, CSV export, config
- **Local-first** — memory stored in `local_memory/` as JSON, atomic writes prevent corruption, nothing leaves your machine

## Architecture

```
User input
    ▼
┌─────────────────────────────────────┐
│  Perception Network (7 layers)      │
│  emotion → task → interpersonal     │
│  → complexity → concise → tone      │
│  → energy                           │
└─────────────────────────────────────┘
    ▼
┌─────────────────────────────────────┐
│  Dispatch layer                     │
│  Cabinet (4 schools + 3 patches)    │
│  + 7 skill modules + routing        │
└─────────────────────────────────────┘
    ▼
┌─────────────────────────────────────┐
│  Memory layer (daozhu-mcp · 23 tools)│
└─────────────────────────────────────┘
```

## Installation (Claude Code)

1. **Copy the skill and MCP server into your project:**
   ```bash
   cp -r skills/daozhu   <your-project>/.claude/skills/daozhu
   cp -r mcp             <your-project>/.claude/daozhu-mcp
   ```

2. **Install Python dependencies** (for the memory layer):
   ```bash
   pip install -r .claude/daozhu-mcp/requirements.txt
   ```

3. **Configure MCP:** copy `.mcp.json.example` to `.mcp.json` at your project root and edit paths.

4. **Trust the project MCP servers** — add to `.claude/settings.local.json`:
   ```json
   { "enableAllProjectMcpServers": true }
   ```
   > ⚠️ Note for VSCode extension environments: Claude Code reads the repo-root `.mcp.json`, **not** `.claude/mcp.json`.

5. **Optional:** reference it in your `CLAUDE.md`:
   ```markdown
   All conversations are dispatched by the `daozhu` skill — see `.claude/skills/daozhu/SKILL.md`.
   ```

6. **Reload Window**, run `/mcp`, confirm `daozhu` shows **Connected**.

## Quick Start

| You say | 道樞 does |
|---------|-----------|
| "I'm so frustrated / exhausted" | Taoism + Buddhist patch, `【感知：情緒低落】` |
| "How do I deal with my professor/teammate" | Confucian external + Strategist |
| "Should I take this project?" (complex) | Cabinet meeting (5 stages) |
| "Help me plan my study schedule" | Work Guide (4 phases) |
| "Lunch cost 150" | Expense log + auto-categorize |
| "I'm feeling down today" | Mood journal + classification + streak detection |
| "How was my week?" | Weekly report + energy insight |
| "System status" | Memory-store health check |

## Command Reference

| Command | Function |
|---------|----------|
| `/儒家` / `/道家` / `/法家` / `/縱橫家` | Switch school manually |
| `/會議 [question]` | Force a cabinet meeting |
| `/工 [task]` / `/工 急` / `/工 深` / `/工 程式` | Work Guide |
| `/費曼` `/蘇格拉底` `/張愛玲` … | Summon a virtual master |
| `/[musician]` / `/播 [mood]` | Music companion |
| `/卦` `/塔羅` `/星盤` `/風水` `/星` `/夢` `/緣` | Metaphysical mirror (7 modes) |
| `/節氣` | Solar-term wellness reminder |
| `/兵` `/辯` `/觀` | Force Military/Mohist/Buddhist patch |
| `/外治` `/內修` `/域` | Legalist domain switch |
| `/藏` | Save a strategy to the vault |
| `/快` / `/慢` | Toggle concise mode |

## Routing to Your Own Skills

When the perception network detects an explicit **creation/development** request, it routes to your project's existing skills (writing, game dev, web, debugging…) per `skills/daozhu/workflows/routing-workflow.md`. Routed skills become 道樞's own modules — handed off with perception context, their internal flow untouched. If no matching skill exists, the cabinet responds instead.

## Memory Layout (`local_memory/`)

```
local_memory/
├── daily/          # expenses, health, reminders, shopping, moods, notes, decisions
└── daozang/        # per-school strategy vault
```

## Configuration (`config.yaml`, optional)

Copy `mcp/config.yaml.example` to `mcp/config.yaml` to override:
- `timezone` — display timezone
- `currency` — expense currency symbol (`TWD`/`HKD`/`USD`/`JPY`/`CNY`/`EUR`/`GBP`/`KRW`)
- `review_weekday` / `review_time` — weekly-report schedule
- `energy_analysis_days` — days needed before energy analysis is produced
- `high_speed_threshold` — concise-mode trigger threshold (words/min, used by the dispatch layer)

`yaml` is an optional dependency — without it, defaults are used silently.

## Development

```bash
cd mcp
pip install -r requirements.txt
python -m pytest tests/          # 31 tests across 4 suites
python server.py                 # run MCP server over stdio
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## License

[Apache License 2.0](LICENSE) — see [NOTICE](NOTICE) for the project authors.
