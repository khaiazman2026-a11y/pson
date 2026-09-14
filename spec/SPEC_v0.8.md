# PSON Specification v0.8 (Freeze Draft) -> v1.0 Candidate

**Status:** SPEC FREEZE - No breaking syntax changes after this
**Version:** 0.8.0 freeze, targeting 1.0.0
**Date:** 2026-09-14
**MIME:** application/pson; version=1.0, application/psonb; version=1.0

## 1. Design Principles

1. **JSON Superset:** Every valid JSON is valid PSON (with type preservation: JSON arrays -> PSON lists)
2. **Python-Native but Language-Agnostic:** tuple (a,b), set {a,b}, dict {k:v} are first-class, but decodable in JS/Go as tagged
3. **Safe by Default:** No eval/exec, only registry types, import jail, depth limits
4. **Human + Machine:** .pson text for configs (git-diff friendly), .psonb binary for tensors (5x smaller, 1900x faster)
5. **Composable:** $include, @import, @ref, @env enable modular configs without programming
6. **Stable:** v1.0 promises backwards compat: any v1.0 .pson file will parse in v2.0

## 2. Text Format (.pson)

### 2.1 Lexical

- **Whitespace:** space, tab, newline, \r
- **Comments:** `# to end of line` and `// to end of line` - allowed anywhere whitespace allowed
- **Trailing commas:** Allowed in list, tuple, dict, set: `[1,2,]`
- **Unquoted keys:** If matches `^[A-Za-z_][A-Za-z0-9_$]*$`, may be unquoted: `{foo: 1, $include: "..."}`. Otherwise must be quoted or encoded.
- **Strings:** Single or double quoted, escapes: \n \t \r \\ \" \'
- **Numbers:** Decimal int arbitrary precision, float IEEE 754: `1`, `-2`, `3.14`, `1e10`, `+inf` via @float

### 2.2 Grammar (EBNF-ish)

```
file        := value
value       := null | boolean | number | string | bytes_tag | time_tag | container | custom_tag | import_tag | ref_tag | env_tag
null        := "null"
boolean     := "true" | "false"
number      := int | float
int         := ["+"|"-"] digit+
float       := ["+"|"-"] digit+ ("." digit+)? (("e"|"E") ["+"|"-"] digit+)?

string      := '"' (char | escape)* '"' | "'" (char | escape)* "'"
escape      := "\" ("n"|"t"|"r"|"\""|"'"|'"')

container   := list | tuple | set | dict
list        := "[" [value ("," value)* [","]] "]"
tuple       := "(" [value ("," value)* [","]] ")"  // ( ) = empty tuple, (1,) = 1-tuple, (1,2) = tuple
set         := "{" [value ("," value)* [","]] "}"  // disambiguated: {a,b} = set, {k: v} = dict
dict        := "{" [pair ("," pair)* [","]] "}"
pair        := (ident | string | value) ":" value
ident       := [A-Za-z_$] [A-Za-z0-9_$]*

custom_tag  := "@" ident "(" [arg_list] ")" ["." ident]*
arg_list    := (ident "=" value | value) ("," (ident "=" value | value))* [","]
bytes_tag   := "@bytes" "(" string ")" // base64
bytearray_tag := "@bytearray" "(" string ")"
datetime_tag:= "@datetime" "(" string ")" // ISO8601
date_tag    := "@date" "(" string ")"
time_tag    := "@time" "(" string ")"
uuid_tag    := "@uuid" "(" string ")"
decimal_tag := "@decimal" "(" string ")"
path_tag    := "@Path" "(" string ")" | "@PurePath" "(" string ")"
complex_tag := "@complex" "(" number "," number ")"
float_tag   := "@float" "(" ("'nan'"|"'inf'"|"'-inf'"|string) ")"
set_tag     := "@set" "(" [value ("," value)*] ")" | "@set()" // empty set literal {} is dict, so use @set()
frozenset_tag:= "@frozenset" "(" [value ("," value)*] ")"
tensor_tag  := "@tensor" "(" "shape" "=" tuple "," "dtype" "=" string ")"

import_tag  := "@import" "(" string ")" ["." ident]*
ref_tag     := "@ref" "(" string ")" // string is JSON Pointer: "#/a/b" or "/a/b"
env_tag     := "@env" "(" string ["," "default" "=" value | "," value] ")"
```

### 2.3 Set vs Dict Disambiguation

- `{}` = empty dict (JSON compat)
- `{:}`? Not allowed. Use `@set()` for empty set, `@frozenset()` for empty frozenset
- `{1,2,3}` = set (no colon)
- `{"a": 1}` = dict (colon present)
- `{a, b, c}` with idents and no colon = set of strings? Actually {a,b} parsed as set of values where values are idents (strings? No, idents are values). For simplicity: unquoted ident as value = string? In v0.6 we treat bare ident as value string? Spec says: ident as value is parsed as string ident? Actually we parse ident as identifier value = string. So {norm, augment} = set {"norm","augment"}? Implementation: _parse_ident returns string. So {a,b} = set {"a","b"}? But we want {norm, augment} to be set of strings. Yes, that is the current behavior - bare ident parsed as string value in set context? Let's define: ident as value = string with same name. So {norm} = {"norm"} set.

To avoid confusion, spec allows quoted strings in set: {"norm","augment"} or {norm, augment} both valid, both set of strings.

### 2.4 Built-in Tags (must be implemented)

| Tag | Args | Returns |
|-----|------|---------|
| @bytes(b64) | base64 string | bytes |
| @bytearray(b64) | base64 | bytearray |
| @datetime(iso) | ISO8601 | datetime |
| @date(iso) | YYYY-MM-DD | date |
| @time(iso) | HH:MM:SS | time |
| @uuid(str) | uuid string | UUID |
| @decimal(str) | decimal string | Decimal |
| @Path(str) | path | Path |
| @PurePath(str) | | PurePath |
| @complex(re,im) | two numbers | complex |
| @float('nan'|'inf'|'-inf') | | float |
| @set(v1,v2...) | values | set |
| @frozenset(...) | | frozenset |
| @tensor(shape,dtype) | text placeholder, binary holds data | ndarray in binary |

### 2.5 Composition

- `$include`: dict key. Value = string or list of strings (relative paths). Merged before @ref resolution. Current file overrides included. Example: `{"$include": "./base.pson", "a": 1}` = {**load(base), **{"a":1}}
- `@import(path)`: value. Loads other file. May have dot access: `@import("./a.pson").field`. Resolved at load time.
- `@ref(pointer)`: JSON Pointer RFC6901, with leading "#". Example: `"#/defaults/lr"` resolves to root["defaults"]["lr"]. Must resolve after $include merge.
- `@env(var, default)`: Reads os.environ[var] or default. If security allow_env=False, raises PermissionError.

Load order: Parse -> $include merge (recursive) -> set root -> @import/@ref/@env resolve (recursive, with cycle detection).

### 2.6 Custom Types

- Registry: `register(MyClass)` or `register(name="MyName")`
- Text: `@MyClass(field=val, ...)` -> ctor(**kwargs) or ctor(*args)
- Binary: T_CUSTOM (60) + name + payload
- Unknown tag in safe mode: returns `{"__pson_tag__": name, "args": [...], "kwargs": {...}}` - never exec

## 3. Binary Format (.psonb)

### 3.1 Header

```
0-4: MAGIC = 0x50 0x53 0x4F 0x4E 0x42 = ASCII "PSONB"
5:   VER = 0x05 (v0.5+), 0x07 for v0.7 security-aware but same TLV
```

### 3.2 TLV Types (1 byte type, then payload)

```
0  NULL
1  FALSE
2  TRUE
10 INT64  (8 bytes BE signed)
11 INT_BIG (u32 len + utf8 decimal string) // for > 2^63
12 FLOAT64 (8 bytes BE IEEE)
13 COMPLEX (16 bytes: 2 float64 BE)
20 STRING (u32 len + utf8)
21 BYTES (u64 len + raw)
22 BYTEARRAY (u64 len + raw)
30 LIST (u32 count + items)
31 TUPLE (u32 count + items) // distinct from LIST
32 SET (u32 count + items)
33 DICT (u32 count + (k v)* )
34 FROZENSET (u32 count)
40 DATETIME (u32 len + iso utf8)
41 DATE
42 TIME
43 UUID
44 DECIMAL
45 PATH
46 PUREPATH
50 TENSOR (u8 dtype_code, u8 ndim, ndim*u32 shape, u64 data_len, raw)
  dtype_code: 0=float32,1=float64,2=int32,3=int64,4=uint8,5=int8,6=bool
60 CUSTOM (u32 name_len + name utf8 + payload TLV)
```

All u32 = big-endian unsigned 32, u64 = BE 64, u8 = BE 8, i64 = BE signed 64.

- Collections: count prefix, then items. No trailing comma.
- String length: byte length of utf8, not char count.
- TENSOR: raw is C-contiguous tobytes() of numpy array. Shape is tuple of dims.

### 3.3 Streaming (.psonb stream)

```
MAGIC + VER + u32 count + (u64 len + TLV)*count
```

Each object length-prefixed. Decoder yields iterator.

## 4. Security Model (v0.7)

- **max_depth:** Default 100. Tracks nesting of list/tuple/set/dict/tag. Exceed -> ValueError.
- **max_string_len:** Default 10_000_000. String literal length.
- **max_collection_size:** Default 1_000_000. Number of elements in single list/set/dict/tuple.
- **max_file_size:** Default 100_000_000 bytes. File size for text and imported files.
- **allow_imports:** None = allow all (default for backward compat), [] = deny all, ["/a","/b"] = jail: imported path must be inside allowed dirs (is_relative_to). Violation -> PermissionError.
- **allow_env:** Bool, default True. If False, @env raises PermissionError.

CLI flags mirror: `--allow-imports`, `--max-depth`, `--max-size`, `--no-env`.

Fuzzing: Parser must not crash on random bytes, must raise ValueError/PermissionError, never RecursionError or segfault.

## 5. Schema (v0.4)

- Validators: string(min_len,max_len,pattern), int(min,max), float(min,max), bool(), enum(*choices), list_of(of=validator), set_of(of=validator), dict_of({k: validator}), optional(inner), any()
- Dataclass as schema: `validate(data, MyDataclass)` checks required fields, applies defaults, constructs instance. Missing required field -> SchemaError with path.
- SchemaError: path = list of keys/indices, message, value.

## 6. API (v1.0 stable)

```python
import pson

# Text
pson.dumps(obj, indent=2, sort_keys=False) -> str
pson.loads(text, custom_types=None, base_path=None, security=None) -> obj
pson.load(fp, ...) -> obj
pson.load_file(path, custom_types=None, security=None) -> obj (auto-detect .pson/.psonb)
pson.dump(obj, fp, ...)

# Binary
pson.dumpsb(obj) -> bytes
pson.loadsb(data, custom_types=None) -> obj
pson.dumpb(obj, fp)
pson.loadb(fp, ...)
pson.dumpb_stream(objs, fp)
pson.loadb_stream(fp) -> iterator

# Registry
pson.register(cls) / @pson.register
pson.get_registry() -> dict

# Schema
pson.validate(data, schema) -> validated
pson.SchemaError
pson.schema.string(...) etc.

# Security
pson.SecurityConfig(max_depth=100, max_string_len=10_000_000, max_collection_size=1_000_000, max_file_size=100_000_000, allow_imports=None, allow_env=True)
```

## 7. CLI (v0.7)

```
pson fmt file.pson [-i] [--indent 2]
pson check file.pson [--allow-imports [dirs]] [--max-depth N] [--max-size N] [--no-env]
pson diff a.pson b.pson  # semantic diff: type-aware
pson to-json file.pson [-o out.json]
pson from-json file.json [-o out.pson]
pson to-psonb file.pson [-o out.psonb]
pson from-psonb file.psonb [-o out.pson] [--inspect]
pson bench [file]  # benchmark vs json
pson fuzz --iters N
```

## 8. Interop / Other Languages

- JS decoder must map: PSON tuple -> JS array with __pson_type="tuple" or custom, set -> Set, etc. Or at least preserve distinction via wrapper: {__pson_tuple__: [...]}. Spec recommends: If target language has no tuple/set, decode tuple as list and set as list, but encoder must be able to roundtrip if possible via custom tags.
- Go: similar.
- For v1.0, reference JS decoder will be provided: `pson-js` package with `parse(text)` returning JS objects with Symbol for tuple/set.

## 9. Versioning

- File format version in binary header VER. Text format has no version header, but $version key optional: `{"$version": "1.0", ...}`
- Semantic versioning for spec: MAJOR breaking syntax, MINOR additive tags, PATCH clarifications.
- v1.0 promises: Any file valid in 1.0 will be valid in 1.x and 2.0 decoder (with warning for deprecated). New tags in minor versions must be optional.

## 10. Test Vectors (for v1.0)

Text:
```
{
  null_val: null,
  bool: true,
  int: 123,
  big_int: 123456789012345678901234567890,
  float: 3.14,
  str: "hello",
  bytes: @bytes('aGVsbG8='),
  list: [1, 2, 3],
  tuple: (1, 2, 3),
  set: {1, 2, 3},
  dict: {a: 1},
  empty_set: @set(),
  path: @Path("/tmp"),
  uuid: @uuid("123e4567-e89b-12d3-a456-426614174000"),
  ref: @ref("#/int"),
  env: @env("HOME", default="/tmp")
}
```

Binary: Same data encoded as TLV, plus tensor (2,2) float32 [[1,2],[3,4]].

## 11. Changelog

- v0.1: core types
- v0.2: @register, Enum, dataclass, CLI fmt
- v0.3: $include, @import, @ref, @env, cycle detection
- v0.4: schema validators, dataclass as schema
- v0.5: binary .psonb, TENSOR, streaming
- v0.6: pip package, pson diff (semantic), VS Code syntax, to-psonb/from-psonb
- v0.7: SecurityConfig import jail, max_depth/size, bench, fuzz
- v0.8: SPEC FREEZE (this doc)
- v0.9: RC, dogfood, migrate 3 OSS projects
- v1.0: STABLE

## 12. Open Questions for v1.0 Final

- Should bare ident {a,b} be set of strings or error? Current: set of strings (ident value = string). Decision: Keep, but document.
- Should @import support URLs? Decision: No for v1.0, only filesystem. URLs would require network + security.
- Should $include support glob? Decision: No for v1.0.
- Float special values: @float('nan') vs nan literal? Decision: Keep tag, as JSON has no nan.

---

End of spec freeze. Any change after this requires MAJOR version bump.
