# WHY_NO_PIP.md - Why PSON is Single File, No pip

## TL;DR
**PSON is one file. Drop it. Fork it. Make your own flavor. No pip needed.**

> pip is for black boxes. PSON is for hackers.

---

## 1. The Problem with pip

```bash
pip install cool-lib
import cool_lib
# What does it do? Where is it? Can I change it?
# It's hidden in site-packages, 50 files, dependencies, Rust build fails on Termux...
```

Termux error we just hit:
```
error: metadata-generation-failed
Target triple not supported: aarch64-unknown-linux-android
Rust toolchain not found
```
**pip failed for a 42KB pure Python file that needs zero deps.** That's insane.

## 2. PSON Philosophy - SQLite Model

SQLite is 1 file, 1M lines, used by billions, no pip:
- You can read it
- You can vendor it
- You can fork it
- You can audit it

PSON same:
- **42KB, 1 file, zero deps**
- `PSON_ALL_IN_ONE.py` - you can open in Termux vim and edit
- No hidden magic, no site-packages, no Rust

## 3. Make Your Own Flavor

This is THE point.

### Example: You want PSON for your game?

```python
# Open PSON_ALL_IN_ONE.py, add 10 lines:
# At bottom, add your custom tag:

@pson.register
class Vector2:
    def __init__(self, x, y): self.x, self.y = x, y
    def __pson__(self): return {"x": self.x, "y": self.y}

# Now your PSON:
# {
#   player_pos: @Vector2(100, 200),
#   enemies: {(0,0), (100, 100)}  # set of tuples
# }

# You just made YOUR flavor: pson-game
# Save as PSON_GAME.py, ship with your game
# No need to PR to us, no pip version conflict
```

### Example: LLM team wants special types?

```python
# Add @LoRA tag for your LLM configs:
@pson.register(name="LoRA")
class LoRA:
    def __init__(self, r, alpha): ...
    
# {
#   model: @LoRA(r=8, alpha=16),
#   image_size: (224, 224)
# }
# That's your flavor: pson-llm
```

**pip kills this.** If it's pip installed, user won't edit site-packages. They will open issue: "pls add Vector2 support". We say no, they fork, pip conflict.

Single file: **just edit the file.** Done. Your flavor, your repo.

## 4. Benefits of No pip

| With pip | Single file (PSON) |
|----------|-------------------|
| `pip install pson` fails on Termux (Rust) | `curl -O PSON_ALL_IN_ONE.py` works everywhere |
| Hidden in `site-packages` | Visible in your repo |
| `import pson` - which version? | `import PSON_ALL_IN_ONE as pson` - you know which file |
| Can't edit, need fork + publish | Edit directly, save as `my_pson.py` |
| Dependency hell | Zero deps, zero hell |
| Need `pyproject.toml`, `setup.py`, build | No build, just copy |
| Audit? 50 files | Audit? 1 file, 42KB, read in 30min |

## 5. When to use pip then?

Never for core. But if you REALLY want:

We provide `pyproject.toml` in `pson_playground`, not in core. Core stays clean.

Core repo `pson` = single file philosophy.
Playground repo `pson_playground` = pip, integrations, flask, fastapi, examples.

**Core = hackable. Playground = convenience.**

## 6. The Real Power: Vendor

Best practice for production:

```bash
# Don't pip install, vendor!
cp PSON_ALL_IN_ONE.py my_project/libs/
git add my_project/libs/PSON_ALL_IN_ONE.py
# Now your project has PSON locked, no external dep
# You can modify libs/PSON_ALL_IN_ONE.py for your needs
# Git tracks it
```

This is how big companies do it. Google vendors SQLite. You vendor PSON.

## 7. Conclusion

> **PSON is not a library. It's a starting point.**

We give you 42KB of clean Python that preserves tuple & set.
You make it yours.

- Want JSON compatible? Fork and remove tuple syntax.
- Want YAML-like? Add indentation sensitivity.
- Want super fast? Replace parser with C extension in your flavor.
- Want Unity? Port to C#.

**All possible because it's one file you own.**

pip makes it "someone else's code".
Single file makes it "your code".

That's why NO PIP.

---

### FAQ

**Q: But how do I install?**
```bash
curl -O https://raw.githubusercontent.com/khaiazman2026-a11y/pson/main/PSON_ALL_IN_ONE.py
```

**Q: What about versioning?**
Git tag your vendored file. `PSON_ALL_IN_ONE.py v1.0.0` in comment. Simple.

**Q: Will you publish to PyPI?**
Maybe in playground, but core will always stay single file. PyPI is convenience, not philosophy.

**Q: Can I make my own flavor and publish?**
YES! Please do:
- `pson-unity` - C# port
- `pson-game` - with Vector2, Color
- `pson-llm` - with LoRA, Tensor
- `pson-termux` - extra Termux friendly

Name it `pson-<your-flavor>`, credit original, and go.

---

**PSON v1.0 - One file to rule them all, and in the darkness bind your own flavor.**

