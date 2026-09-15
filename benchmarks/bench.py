"""
Benchmark PSON vs JSON vs msgpack - v0.9.0-beta
Run: python benchmarks/bench.py
"""
import time, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PSON_ALL_IN_ONE as pson

try:
    import msgpack
    HAS_MSGPACK=True
except:
    HAS_MSGPACK=False

data = {
    "model": "llama3.2-vision",
    "image_size": (224, 224),
    "tags": {"vision", "llm", "malay"},
    "layers": [{"id": i, "shape": (768, 768)} for i in range(100)],
    "history": [("user", f"msg {i}") for i in range(100)]
}

def bench(name, fn):
    s=time.time()
    for _ in range(1000):
        fn()
    e=time.time()-s
    print(f"{name}: {e:.3f}s")
    return e

print("=== PSON v0.9.0-beta adoption benchmark ===")
print(f"Data keys: {len(data)}, layers: 100")

json_str = json.dumps(data, default=lambda o: list(o) if isinstance(o, (set, tuple)) else str(o))
pson_text = pson.dumps(data)
pson_bin = pson.dumpsb(data)

print(f"\nSize: JSON {len(json_str)} B | PSON text {len(pson_text)} B | PSONB {len(pson_bin)} B")
print(f"PSONB is {len(json_str)/len(pson_bin):.1f}x smaller than JSON")

bench("json dumps", lambda: json.dumps(data, default=lambda o: list(o) if isinstance(o, (set, tuple)) else str(o)))
bench("pson dumps", lambda: pson.dumps(data))
bench("pson dumpsb", lambda: pson.dumpsb(data))
bench("json loads", lambda: json.loads(json_str))
bench("pson loads", lambda: pson.loads(pson_text))
bench("pson loadsb", lambda: pson.loadsb(pson_bin))

print("\n✅ Tuple preserved:", isinstance(pson.loads(pson_text)["image_size"], tuple))
print("✅ Set preserved:", isinstance(pson.loads(pson_text)["tags"], set))

