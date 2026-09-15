
"""
tests/test_core.py - Core v1.0 tests - tuple/set preserved
Run: pytest tests/test_core.py -v
"""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import PSON_ALL_IN_ONE as pson

def test_tuple_preserved():
    data = {"image_size": (224, 224)}
    s = pson.dumps(data)
    out = pson.loads(s)
    assert out["image_size"] == (224, 224)
    assert isinstance(out["image_size"], tuple)
    print("✅ tuple preserved")

def test_set_preserved():
    data = {"tags": {"a", "b", "c"}}
    s = pson.dumps(data)
    out = pson.loads(s)
    assert out["tags"] == {"a", "b", "c"}
    assert isinstance(out["tags"], set)
    print("✅ set preserved")

def test_nested_tuple_set():
    data = {
        "size": (224, 224),
        "tags": {"flask", "pson", "v1.0"},
        "model": {"layers": [(3, 3), (5, 5)]}
    }
    s = pson.dumps(data, indent=2)
    out = pson.loads(s)
    assert out["size"] == (224, 224)
    assert out["tags"] == {"flask", "pson", "v1.0"}
    assert out["model"]["layers"][0] == (3, 3)
    print("✅ nested tuple/set")

def test_json_comparison():
    """JSON loses tuple/set, PSON keeps"""
    import json
    data = {"size": (224, 224)}
    j = json.dumps(data)  # tuple becomes list
    j_out = json.loads(j)
    assert isinstance(j_out["size"], list)  # JSON loses

    p = pson.dumps(data)
    p_out = pson.loads(p)
    assert isinstance(p_out["size"], tuple)  # PSON keeps
    print("✅ PSON vs JSON")

def test_roundtrip_file():
    p = ROOT / "test.pson"
    data = {"app": "test", "size": (224, 224), "tags": {"a", "b"}}
    p.write_text(pson.dumps(data), encoding="utf-8")
    out = pson.load_file(str(p))
    assert out["size"] == (224, 224)
    p.unlink(missing_ok=True)
    print("✅ file roundtrip")

if __name__ == "__main__":
    test_tuple_preserved()
    test_set_preserved()
    test_nested_tuple_set()
    test_json_comparison()
    test_roundtrip_file()
    print("\nAll core tests passed - ready for v1.0")

