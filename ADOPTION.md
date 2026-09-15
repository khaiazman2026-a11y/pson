# PSON v0.9.0-beta - Adoption Guide

This is the **pre-1.0 beta** for public testing. Combined v0.8+v0.9.

## Why try now?
- Tuple `(224,224)` stays tuple, not list (critical for vision models)
- Set `{a,b}` stays set
- Binary `.psonb` 3-5x smaller than JSON, 2x faster loads
- Zero deps, single file
- Flask + FastAPI ready

## Install (pip local)
```bash
pip install -e .
# or
pip install PSON-ALL-IN-ONE==0.9.0b0
```

## Quick start for testers
```python
import PSON_ALL_IN_ONE as pson

cfg = pson.load_file("config.pson") # with SecurityConfig
print(cfg["image_size"]) # (224, 224) tuple!

# binary for cache
pson.dumpb(cfg, open("config.psonb","wb"))
```

## What we need from you (testers)
1. Does `pson.loads(dumps(obj)) == obj` for your data? (tuple/set)
2. Any crash? Report with `SecurityConfig` off
3. Size/speed vs JSON for your LLM config

## Roadmap to v1.0
- v0.9.0-beta = this (adoption)
- v1.0 = spec frozen, no breaking changes

Test and open issue: https://github.com/khaiazman2026-a11y/pson/issues

