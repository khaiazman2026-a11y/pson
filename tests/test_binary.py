
"""
tests/test_binary.py - PSONB binary roundtrip
"""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PSON_ALL_IN_ONE as pson

def test_binary_roundtrip():
    data = {
        "size": (224, 224),
        "tags": {"a", "b"},
        "list": [1,2,3],
        "nested": {"x": (1,2)}
    }
    b = pson.dumpsb(data)
    assert b[:5] == b'PSONB'
    out = pson.loadsb(b)
    assert out["size"] == (224, 224)
    assert out["tags"] == {"a", "b"}
    print(f"✅ binary {len(b)} bytes")

def test_binary_stream():
    objs = [{"a": (1,2)}, {"b": {1,2,3}}]
    import io
    buf = io.BytesIO()
    pson.dumpb_stream(objs, buf)
    buf.seek(0)
    loaded = list(pson.loadb_stream(buf))
    assert loaded[0]["a"] == (1,2)
    assert loaded[1]["b"] == {1,2,3}
    print("✅ stream")

if __name__ == "__main__":
    test_binary_roundtrip()
    test_binary_stream()

