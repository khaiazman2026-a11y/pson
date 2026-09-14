# PSON - Python Serial Object Notation

> Single file. No deps. Tuple & set preserved.

PSON is a JSON-like format that keeps Python types.

```python
# JSON loses type: [224,224] -> list
# PSON keeps it: (224, 224) -> tuple
```

## Test in 10 seconds – Single file

```bash
# 1. Download one file
curl -O https://raw.githubusercontent.com/khaiazman2026-a11y/pson/main/PSON_ALL_IN_ONE.py

# 2. Test
python -c "import PSON_ALL_IN_ONE as pson; print(pson.dumps({'a': (1,2), 'b': {1,2,3}}, indent=2))"
```

No `pip install`. No build. Copy 1 file = done.

## Load

**config.pson**
```pson
{
  model: "vit",
  image_size: (224, 224),
  tags: {classification, detection},
  lr: 0.001
}
```

**load.py**
```python
import PSON_ALL_IN_ONE as pson

cfg = pson.load_file("config.pson")
print(cfg["image_size"])        # (224, 224)
print(type(cfg["image_size"]))  # <class 'tuple'>  <- tuple preserved!
print(cfg["tags"])              # {'classification', 'detection'}
print(type(cfg["tags"]))        # <class 'set'>
```

```bash
python load.py
```

Other loaders:
```python
text = open("config.pson").read()
cfg = pson.loads(text)          # from string
cfg = pson.load(open("config.pson"))  # from file object
```

## Dump

**dump.py**
```python
import PSON_ALL_IN_ONE as pson

data = {
  "model": "vit",
  "image_size": (224, 224),   # tuple
  "tags": {"classification", "detection"},  # set
  "lr": 0.001
}

# py -> pson string
s = pson.dumps(data, indent=2)
print(s)

# py -> pson file
with open("out.pson", "w") as f:
    pson.dump(data, f, indent=2)

# or
with open("out.pson", "w") as f:
    f.write(pson.dumps(data, indent=2))
```

Result `out.pson`:
```pson
{
  model: 'vit',
  image_size: (224, 224),
  tags: {
    'classification',
    'detection'
  },
  lr: 0.001
}
```

Roundtrip:
```python
back = pson.loads(s)
assert back["image_size"] == (224, 224)  # tuple still tuple
```

## What PSON keeps vs JSON

| | JSON | PSON |
|---|---|---|
| `(224,224)` | `[224,224]` list | `(224,224)` tuple |
| `{a,b}` | `["a","b"]` list | `{a,b}` set |
| `# comment` | ❌ | ✅ |
| trailing comma | ❌ | ✅ |

That's it. No magic.

## File

Only need this:

```
PSON_ALL_IN_ONE.py  # ~800 lines, zero deps
```

Import as:

```python
import PSON_ALL_IN_ONE as pson
```

## Status

v0.6.0 – works for load/dump. Binary and security features in progress.

