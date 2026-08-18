# Contributing to 道樞 Dàoshū

Thanks for your interest in contributing! 道樞 is an Eastern-philosophy AI orchestration framework — the more minds it carries, the wiser it gets.

## How to contribute

- **Report bugs / request features** — open an issue describing the expected vs actual behavior.
- **Improve docs** — typos, clearer installation, better examples: all welcome.
- **Add a skill module** — new ministers, patches, or modules under `skills/daozhu/`.
- **Improve the memory layer** — new tools in `mcp/`, better storage, more tests.
- **Translate** — README is bilingual (EN / zh-TW); help keep both in sync.

## Development setup

```bash
git clone https://github.com/ddg94360-code/daozhu.git
cd daozhu
pip install -r mcp/requirements.txt
python -m pytest mcp/tests/    # all tests must pass
```

The MCP server runs over stdio — `python mcp/server.py` (from the repo root, or `cd mcp && python server.py`) and test with any MCP client, or call the underlying functions directly.

Optional dashboard (also from the repo root):

```bash
pip install -r mcp/requirements-web.txt
python -m pytest web/tests/
```

New HTTP routes must call `daily` / `weekly` / `solarterm` / `daozang` / `xinjing_render` — never write `local_memory` JSON from `web/`. Cabinet seating and perception lights are pure functions.

## Code style

- **Python** (`mcp/`): type hints on every public function, a one-line docstring in Traditional Chinese, no dead code. Follow the existing module patterns (`memory_store` as the shared bottom layer; `daily`/`weekly`/`daozang`/`solarterm` as feature modules; `server` as a thin `_TOOLS` registry). Freeze time in tests by patching `memory_store._wall_clock`, not `datetime.now` or the `daily.now` alias.
- **Skill files** (`skills/`): Markdown specs, Traditional Chinese, one topic per file under `ministers/`, `patches/`, `modules/`, `workflows/`. Keep output-format sections imperative and concrete.

## Testing

New memory-layer features must ship with pytest coverage. Add tests to `mcp/tests/` — the `isolated_memory` fixture (in `conftest.py`) isolates the JSON store into a temp dir via the `DAOZHU_MEMORY_DIR` env var.

## Pull request checklist

- [ ] `python -m pytest tests/` passes (all suites)
- [ ] New Python functions have type hints + docstrings
- [ ] New MCP tools are registered in `server._TOOLS`
- [ ] README command table updated if commands changed
- [ ] CHANGELOG entry added under Unreleased

## License

By contributing, you agree your contributions are licensed under [Apache 2.0](LICENSE).
