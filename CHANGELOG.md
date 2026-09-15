# Changelog - PSON

All notable changes to PSON will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-05-13 - CORE ONLY STABLE

### Added
- **Core Freeze**: `PSON_ALL_IN_ONE.py` 42KB, zero deps, single file - freeze API
- `__all__` defined: dumps, loads, dump, load, load_file, dumpsb, loadsb, dumpb, loadb, dumpb_stream, loadb_stream, SecurityConfig, etc
- `__version__ = "1.0.0"`
- Binary format `PSONB` freeze: MAGIC `b'PSONB'` + VER `1` - forever
- Tests: `tests/test_core.py` (tuple/set preservation), `test_binary.py`, `test_security.py` - all passed
- Spec: `PSON_SPEC_v1.0.md` - freeze spec
- Docs: `README.md` v1.0 - why tuple/set matters for LLM
- `pyproject.toml` v1.0 - `pip install pson`, CLI `pson`

### Changed
- **BREAKING**: Repo `pson` now CORE ONLY - only `PSON_ALL_IN_ONE.py` + docs + tests
- Integrations moved to `pson_playground`: `integrations/flask/`, `integrations/fastapi/`, `examples/`, `flask_pson/`
- Version bump from `0.9.0-beta` -> `1.0.0`
- Cleaned legacy files: `PSON_ALL_IN_ONE_*.py`, `pson_v*.py`, `integration/` old

### Why v1.0?
- JSON loses types: `(224,224)` -> `[224,224]`, `{"a","b"}` -> `["a","b"]`
- PSON preserves: tuple `()` and set `{}` - critical for LLM configs
- Example: `image_size: (224, 224)`, `stop_tokens: {<|im_end|>, <|end|>}`
- 5 days roadmap done: Freeze Core, Security, Tests, Docs, Release

---

## [1.0.0-rc1] - 2026-05-13 - Release Candidate

### Added
- `__all__` added
- Version `1.0.0-rc1` in `PSON_ALL_IN_ONE.py`
- Tests: `tests/test_core.py` - 5 tests: tuple preserved, set preserved, nested, JSON vs PSON, file roundtrip - all ✅
- `PSON_SPEC_v1.0.md` generated
- `README_v1.0.md` generated
- `pyproject.toml` v1.0.0 ready for PyPI

### Changed
- Core only cleaning: deleted `integration/`, `integrations/`, `examples/`, `flask_pson/`
- Bulletproof Path: `_find_pson_root()` walk up until `PSON_ALL_IN_ONE.py` found

---

## [0.9.0-beta] - 2026-05-12

### Added
- Binary format: `dumpsb`/`loadsb` with `MAGIC = b'PSONB'` + `VER`
- `dumpb_stream`/`loadb_stream` for multiple objects
- Tensor support: numpy `T_TENSOR` with dtype, shape
- `PSON_SPEC_v0.8_FREEZE.md`

### Changed
- Flask integration bulletproof path fix: absolute path next to file, no relative guessing
- `flask_pson` shim fallback if `integrations` missing
- Examples: `examples/llm_app/flask_app.py` with LLM config

---

## [0.7.0-alpha] - 2026-05-10 - Security Enforced

### Added
- `SecurityConfig`: `max_depth=64`, `max_size=10MB`, `max_keys=10000`, `max_array_len=100000`, `allow_imports`
- `SecurityError` raised when exceeded
- `DEFAULT_SECURITY` global
- `PSONDecoder` tracks depth
- `loads`/`load_file`/`loadsb` check size
- Ready for v1.0 audit

### Security
- Enforced by default, can be customized or disabled with `allow_imports=False`

---

## [0.6.0] - 2026-05-01 - Initial Public

### Added
- Single file `PSON_ALL_IN_ONE.py` <50KB
- Text format: tuple `()`, set `{}`, list `[]`, dict `k: v`
- Tags: `@Type(args)`, `@import`, `@ref`, `@env`, `@bytes`, `@Path`, `@datetime`
- Imports: `$include`
- Comments: `#`, `//`, `/* */`
- Schema: `String`, `Int`, `Float`, `Bool`, `ListOf`, `SetOf`, `DictOf`, `EnumVal`
- CLI: `pson fmt`, `check`, `diff`, `to-json`, `from-json`, `to-psonb`, `from-psonb`
- `examples/`, `integrations/`

---

## Links
- Core: https://github.com/khaiazman2026-a11y/pson
- Playground: https://github.com/khaiazman2026-a11y/pson_playground
- Spec v1.0: https://github.com/khaiazman2026-a11y/pson/blob/main/PSON_SPEC_v1.0.md

