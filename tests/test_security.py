import PSON_ALL_IN_ONE as pson

def test_max_depth():
    deep = "["*70 + "]"*70
    try:
        pson.loads(deep, security=pson.SecurityConfig(max_depth=10))
        assert False, "should fail"
    except pson.SecurityError:
        pass

def test_max_size():
    try:
        pson.loads("a"*200, security=pson.SecurityConfig(max_size=10))
        assert False
    except pson.SecurityError:
        pass

def test_max_keys():
    big = "{" + ", ".join([f"k{i}: {i}" for i in range(100)]) + "}"
    try:
        pson.loads(big, security=pson.SecurityConfig(max_keys=10))
        assert False
    except pson.SecurityError:
        pass

def test_import_blocked():
    try:
        pson.loads('@import("etc/passwd")', security=pson.SecurityConfig(allow_imports=False))
        assert False
    except pson.SecurityError:
        pass

def test_tuple_set_preserved():
    obj = pson.loads('{(1,2), (3,4)}')
    assert isinstance(obj, set)
    obj2 = pson.loads('(1, 2, 3)')
    assert isinstance(obj2, tuple)

if __name__=="__main__":
    test_max_depth()
    test_max_keys()
    test_import_blocked()
    test_tuple_set_preserved()
    test_max_size()
    print("All security tests passed")

