# PSON - Python Serial Object Notation

> **JSON = JavaScript Object Notation. Python deserves Python Object Notation. That's PSON.**

PSON is type-safe, env-aware, 5.2x smaller than JSON (binary), and safe unlike Pickle.

[![Spec](https://img.shields.io/badge/spec-v0.8%20frozen-blue)]()
[![Version](https://img.shields.io/badge/version-v0.9.0--rc-orange)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Built on](https://img.shields.io/badge/built%20on-Android%20Termux-brightgreen)]()

> **JSON forgets Python. Pickle is unsafe. PSON remembers safely.**

PSON is a human-friendly, type-preserving serialization format. Text `.pson` for configs, Binary `.psonb` for tensors/embeddings.

```python
import PSON_ALL_IN_ONE as pson

# Tuple, Set, Path, datetime - all preserved
pson.dumps({
    "coords": (1, 2, 3),
    "tags": {"python", "ml", "safe"},
    "weights": Path("./model.bin")
}, indent=2)

# {
#   coords: (1, 2, 3),
#   tags: {ml, python, safe},
#   weights: @Path("./model.bin")
# }
```

### Why not JSON / YAML / Pickle / TOML?

| Feature | JSON | YAML | Pickle | TOML | **PSON** |
|---------|------|------|--------|------|----------|
| `tuple` vs `list` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `set` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `Path`, `datetime` | ❌ | ❌ | ✅ | partial | ✅ |
| Safe (no code exec) | ✅ | ❌ | ❌ | ✅ | ✅ |
| `@import` / `@ref` / `$include` | ❌ | ❌ | ❌ | ❌ | ✅ |
| Comments | ❌ | ✅ | ❌ | ✅ | ✅ |
| Binary `.psonb` for tensors | ❌ | ❌ | ❌ | ❌ | ✅ |
| Streaming large arrays | ❌ | ❌ | ❌ | ❌ | ✅ 
- ✅ Preserves Python types: `tuple (224,224)`, `set {a,b}`, `Path`, `datetime`
- ✅ `@env()`, `@Path()`, `$include`, `@ref()` built-in – no dotenv needed
- ✅ Safe – no pickle RCE, import jail
- ✅ PSONB binary 5.2x smaller than JSON|

**Real pain:**
- JSON: `[224, 224]` - is it list or tuple? You lose info. `tuple([224,224])` != `list` in Python.
- YAML: `NO` becomes `False` (Norway problem), significant whitespace breaks.
- Pickle: `pickle.load()` can run arbitrary code - never load untrusted pickle.
- TOML: No tuple, no set, no imports.

PSON fixes all of them.

### Install (v1.0 coming)

For now, single file - no deps:

```bash
# Copy one file into your project
curl -O https://raw.githubusercontent.com/khaiazman2026-a11y/pson/main/PSON_ALL_IN_ONE.py

# Or clone
git clone https://github.com/khaiazman2026-a11y/pson
```

Future:
```bash
pip install pson  # at v1.0
```

### Quick Start

**Text config `.pson`:**

```pson
{
  model: "vit",
  image_size: (224, 224),  // tuple! immutable
  tags: {classification, detection},  // set! unique
  lr: 0.001,
  weights: @Path("./weights.bin"),
  secret: @env("HF_TOKEN"),
  $include: "./common.pson"
}
```

```python
import PSON_ALL_IN_ONE as pson

cfg = pson.load_file("config.pson")
print(cfg["image_size"])  # (224, 224) - tuple preserved!
print(type(cfg["tags"]))  # <class 'set'>

# Safe load untrusted files
from PSON_ALL_IN_ONE import SecurityConfig
cfg = pson.load_file("untrusted.pson", security=SecurityConfig(max_depth=50, allow_imports=[]))
```

**Binary `.psonb` for embeddings/tensors:**

```python
import PSON_ALL_IN_ONE as pson
import numpy as np

emb = np.random.randn(10000, 768).astype('float32')  # 30MB

# Save safe, not pickle
pson.dumpb({"embeddings": emb, "meta": {"model": "bert"}}, open("emb.psonb","wb"))

# Load safe - no code exec ever
data = pson.loadb(open("emb.psonb","rb"))
print(data["embeddings"].shape)  # (10000, 768) dtype preserved

# Streaming for 1M rows without RAM blowup
pson.dumpb_stream([{"emb": emb[i]} for i in range(1000000)], open("big.psonb","wb"))
```

### CLI

```bash
python PSON_ALL_IN_ONE.py fmt config.pson -i
python PSON_ALL_IN_ONE.py check config.pson
python PSON_ALL_IN_ONE.py diff a.pson b.pson  # semantic diff - catches tuple vs list
python PSON_ALL_IN_ONE.py bench  # benchmark vs json/pickle
python PSON_ALL_IN_ONE.py from-json config.json -o config.pson
```

### Migrations (v0.9 RC)

**1. YAML -> PSON**
```yaml
# docker-compose.yml
services:
  web:
    ports: ["80:80"]  # string list, ambiguous
```
```pson
// docker-compose.pson
{
  services: {
    web: { ports: [(80, 80)] }  // tuple pair, type-safe + @env for secrets
  }
}
```

**2. JSON -> PSON (HuggingFace config)**
```json
{ "image_size": [224, 224] }  // list, but should be tuple
```
```pson
{
  image_size: (224, 224),  // tuple preserved
  supported_tasks: {classification, detection}  // set!
}
```

**3. Pickle -> PSONB**
```python
# Before: unsafe
pickle.dump(embeddings, open("emb.pkl","wb"))

# After: safe + same size
pson.dumpb({"emb": embeddings}, open("emb.psonb","wb"))
```
Pickle: 2.93MB, unsafe. PSONB: 2.93MB, safe, preserves dtype.

See [MIGRATION.md](./MIGRATION.md)

### Spec

- Spec frozen at v0.8: [spec/SPEC_v0.8.md](./spec/SPEC_v0.8.md)
- EBNF grammar, TLV binary format
- JS decoder: [spec/pson-js-decoder.js](./spec/pson-js-decoder.js)

### Benchmarks

On Termux (Android phone):

```
JSON  : 158 MB for tensor, loses types
Pickle: 30.8 MB, unsafe
PSONB : 30.7 MB, safe, preserves types
```

Run yourself: `python PSON_ALL_IN_ONE.py bench`

### Roadmap

- [x] v0.7 - Security (import jail, SecurityConfig)
- [x] v0.8 - Spec freeze (EBNF + binary TLV)
- [x] v0.9 RC - Migrations + dogfooding (current)
- [ ] v1.0 - PyPI `pip install pson` + VSCode extension + stable

### Why not JSON?
Flask:
{ image_size: [224,224] } // is it list or tuple? JSON forgets.

PSON:
{ image_size: (224,224) } // tuple preserved, Jinja gets real tuple

ML:
{ classes: {cat, dog} } // JSON can't save set – PSON can

### Why built on Android Termux?

To prove PSON has zero heavy dependencies. If it builds on a phone, it builds anywhere.

Built in Malaysia.

### Contributing

```bash
git clone https://github.com/khaiazman2026-a11y/pson
cd pson
python -m pytest tests/
python PSON_ALL_IN_ONE.py fuzz --iters 1000
```

Open an issue, then PR.

### License

MIT - see [LICENSE](./LICENSE)

---
**Star if JSON ever broke your tuple.**

## Built From Phone
No laptop, no CS degree. Orchestrated in Termux, coded with Meta AI.
Flask integration live at `integration/flask/` – localhost:5000 tested in Malaysia.
