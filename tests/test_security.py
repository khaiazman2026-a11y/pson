
"""
tests/test_security.py
"""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PSON_ALL_IN_ONE as pson

def test_max_depth():
    sec = pson.SecurityConfig(max_depth=3)
    deep = "{" * 10 + "}" * 10
    try:
        pson.loads(deep, security=sec)
        assert False, "should fail"
    except pson.SecurityError:
        print("✅ max_depth blocked")

def test_max_size():
    sec = pson.SecurityConfig(max_size=10)
    try:
        pson.loads("{a: 123456789012345}", security=sec)
        assert False
    except pson.SecurityError:
        print("✅ max_size blocked")

def test_import_blocked():
    sec = pson.SecurityConfig(allow_imports=False)
    try:
        pson.loads('{ $include: "other.pson" }', security=sec)
        assert False
    except pson.SecurityError:
        print("✅ import blocked")

if __name__ == "__main__":
    test_max_depth()
    test_max_size()
    test_import_blocked()

