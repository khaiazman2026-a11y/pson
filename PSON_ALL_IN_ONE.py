#!/usr/bin/env python3
"""
PSON ALL-IN-ONE v0.6.1
Python Serial Object Notation - One file to rule them all

Drop this single file anywhere:
  import PSON_ALL_IN_ONE as pson
  pson.dumps({"coords": (1,2), "tags": {"a","b"}}, indent=2)
  pson.loads('(224, 224)')  # tuple preserved

Features: tuple (), set {}, list [], dict, comments, load/dump
Zero deps.

Version: 0.6.1 (LSP + compat fixes)
Previous: v0.6.0
"""
import re, os, sys, io, json, base64, pathlib, datetime, uuid, decimal, struct, argparse
from dataclasses import is_dataclass, asdict, fields, MISSING
from enum import Enum
from typing import Union, get_origin, get_args

__version__ = "0.6.1"

# ========= REGISTRY =========
_registry = {}
def register(cls=None, *, name=None):
    def decorator(c):
        key=name or c.__name__
        _registry[key]=c
        if not hasattr(c,"__pson__") and is_dataclass(c):
            c.__pson__=lambda self: asdict(self)
        return c
    if cls is None: return decorator
    return decorator(cls)

def get_registry(): return dict(_registry)

# ========= TEXT ENCODER =========
def dumps(obj, indent=2, sort_keys=False):
    return _encode_text(obj, indent, level=0, sort_keys=sort_keys)

def _encode_text(obj, indent, level, sort_keys):
    pad=" "*indent*level if indent else ""; pad1=" "*indent*(level+1) if indent else ""; nl="\n" if indent else ""; sep=",\n" if indent else ", "
    if obj is None: return "null"
    if isinstance(obj, bool): return "true" if obj else "false"
    if isinstance(obj, int) and not isinstance(obj, bool): return str(obj)
    if isinstance(obj, float):
        if obj!=obj: return "@float('nan')"
        if obj==float('inf'): return "@float('inf')"
        if obj==float('-inf'): return "@float('-inf')"
        return repr(obj)
    if isinstance(obj, complex): return f"@complex({obj.real!r}, {obj.imag!r})"
    if isinstance(obj, str): return repr(obj)
    if isinstance(obj, bytes): return f"@bytes({base64.b64encode(obj).decode()!r})"
    if isinstance(obj, bytearray): return f"@bytearray({base64.b64encode(obj).decode()!r})"
    if isinstance(obj, datetime.datetime): return f"@datetime({obj.isoformat()!r})"
    if isinstance(obj, datetime.date) and not isinstance(obj, datetime.datetime): return f"@date({obj.isoformat()!r})"
    if isinstance(obj, datetime.time): return f"@time({obj.isoformat()!r})"
    if isinstance(obj, uuid.UUID): return f"@uuid({str(obj)!r})"
    if isinstance(obj, decimal.Decimal): return f"@decimal({str(obj)!r})"
    if isinstance(obj, pathlib.Path): return f"@Path({str(obj)!r})"
    if isinstance(obj, pathlib.PurePath): return f"@PurePath({str(obj)!r})"
    try:
        import numpy as np
        if isinstance(obj, np.ndarray):
            return f"@tensor(shape={obj.shape!r}, dtype={str(obj.dtype)!r})"
    except Exception: pass
    if isinstance(obj, set):
        if not obj: return "@set()"
        items=sorted(obj, key=lambda x: repr(x)) if sort_keys else list(obj)
        inner=sep.join(_encode_text(x, indent, level+1, sort_keys) for x in items)
        return f"{{{nl}{pad1}{inner}{nl}{pad}}}" if indent else f"{{{inner}}}"
    if isinstance(obj, frozenset):
        if not obj: return "@frozenset()"
        items=sorted(obj, key=lambda x: repr(x)) if sort_keys else list(obj)
        inner=sep.join(_encode_text(x, indent, level+1, sort_keys) for x in items)
        return f"@frozenset({nl}{pad1}{inner}{nl}{pad})" if indent else f"@frozenset({inner})"
    if isinstance(obj, tuple):
        if len(obj)==1: return f"({_encode_text(obj[0], indent, level+1, sort_keys)},)"
        if not obj: return "()"
        inner=sep.join(_encode_text(x, indent, level+1, sort_keys) for x in obj)
        return f"({nl}{pad1}{inner}{nl}{pad})" if indent and len(obj)>2 else f"({inner})"
    if isinstance(obj, list):
        if not obj: return "[]"
        inner=sep.join(_encode_text(x, indent, level+1, sort_keys) for x in obj)
        return f"[{nl}{pad1}{inner}{nl}{pad}]" if indent else f"[{inner}]"
    if isinstance(obj, dict):
        if not obj: return "{}"
        items=obj.items()
        if sort_keys: items=sorted(items, key=lambda kv: str(kv[0]))
        parts=[]
        for k,v in items:
            ek=k if isinstance(k,str) and re.match(r'^[A-Za-z_][A-Za-z0-9_$]*$',k) else _encode_text(k,indent,level+1,sort_keys)
            ev=_encode_text(v,indent,level+1,sort_keys)
            parts.append(f"{ek}: {ev}" if not indent else f"{pad1}{ek}: {ev}")
        return f"{{{nl}{sep.join(parts)}{nl}{pad}}}" if indent else f"{{{', '.join(parts)}}}"
    if isinstance(obj, Enum): return f"@{obj.__class__.__name__}({obj.name!r})"
    if is_dataclass(obj):
        cls_name=obj.__class__.__name__
        if cls_name not in _registry: _registry[cls_name]=obj.__class__
        inner=sep.join(f"{k}={_encode_text(v,indent,level+1,sort_keys)}" for k,v in asdict(obj).items())
        return f"@{cls_name}({nl}{pad1}{inner}{nl}{pad})" if indent else f"@{cls_name}({inner})"
    if hasattr(obj,"__pson__"):
        cls_name=obj.__class__.__name__
        if cls_name not in _registry: _registry[cls_name]=obj.__class__
        data=obj.__pson__()
        if isinstance(data,dict):
            inner=sep.join(f"{k}={_encode_text(v,indent,level+1,sort_keys)}" for k,v in data.items())
            return f"@{cls_name}({nl}{pad1}{inner}{nl}{pad})" if indent else f"@{cls_name}({inner})"
        return f"@{cls_name}({_encode_text(data,indent,level+1,sort_keys)})"
    if hasattr(obj,"__dict__"):
        cls_name=obj.__class__.__name__
        if cls_name not in _registry: _registry[cls_name]=obj.__class__
        inner=sep.join(f"{k}={_encode_text(v,indent,level+1,sort_keys)}" for k,v in obj.__dict__.items() if not k.startswith("_"))
        return f"@{cls_name}({nl}{pad1}{inner}{nl}{pad})" if indent else f"@{cls_name}({inner})"
    raise TypeError(f"Cannot encode {type(obj)}")

# ========= TEXT DECODER + IMPORTS =========
class _ImportRef:
    def __init__(self, path, dotpath): self.path=path; self.dotpath=dotpath
class _Ref:
    def __init__(self, pointer): self.pointer=pointer
class _Env:
    def __init__(self, var, default): self.var=var; self.default=default

class PSONDecoder:
    def __init__(self, text, custom_types=None, base_path=None, _import_stack=None, security=None):
        self.text=text; self.pos=0
        self.custom_types={**_registry, **(custom_types or {})}
        self.base_path=pathlib.Path(base_path).parent if base_path else pathlib.Path(".")
        self._import_stack=_import_stack or set()
        self._root_obj=None
        self.security=security
    def parse(self):
        self._skip()
        val=self._parse_value()
        val=self._merge_includes(val)
        self._root_obj=val
        val=self._resolve(val)
        self._skip()
        return val
    def _merge_includes(self, obj):
        if isinstance(obj, dict) and "$include" in obj:
            inc=obj.pop("$include")
            if isinstance(inc, str): inc=[inc]
            base={}
            for p in inc:
                try:
                    imported=self._do_import(p)
                    if isinstance(imported, dict):
                        base={**base, **imported}
                except FileNotFoundError:
                    # README compat: skip missing includes silently
                    continue
            base={**base, **obj}
            for k in base:
                if isinstance(base[k], dict):
                    base[k]=self._merge_includes(base[k])
            return base
        if isinstance(obj, dict):
            for k in obj:
                if isinstance(obj[k], dict):
                    obj[k]=self._merge_includes(obj[k])
        return obj
    def _resolve(self, obj, seen=None):
        if seen is None: seen=set()
        oid=id(obj)
        if oid in seen: return obj
        seen.add(oid)
        if isinstance(obj, dict):
            for k in list(obj.keys()):
                obj[k]=self._resolve(obj[k], seen)
            if "__pson_tag__" in obj:
                tag=obj["__pson_tag__"]
                if tag=="import":
                    return self._do_import(obj["args"][0] if obj["args"] else "")
                if tag=="ref":
                    return self._resolve_pointer(obj["args"][0] if obj["args"] else "#/")
                if tag=="env":
                    var=obj["args"][0] if obj["args"] else ""
                    default=obj["kwargs"].get("default", obj["args"][1] if len(obj["args"])>1 else None)
                    return os.environ.get(var, default)
            return obj
        if isinstance(obj, (list,tuple,set,frozenset)):
            items=[self._resolve(x, seen) for x in obj]
            if isinstance(obj, list): return items
            if isinstance(obj, tuple): return tuple(items)
            if isinstance(obj, set): return set(items)
            if isinstance(obj, frozenset): return frozenset(items)
        if isinstance(obj, _ImportRef):
            cur=self._do_import(obj.path)
            for part in obj.dotpath:
                cur=cur.get(part) if isinstance(cur, dict) else getattr(cur, part, None)
            return self._resolve(cur, seen)
        if isinstance(obj, _Ref):
            return self._resolve(self._resolve_pointer(obj.pointer), seen)
        if isinstance(obj, _Env):
            return os.environ.get(obj.var, obj.default)
        return obj
    def _do_import(self, rel_path):
        p=(self.base_path / rel_path).resolve()
        if str(p) in self._import_stack: raise ValueError(f"Circular import: {p}")
        if not p.exists(): raise FileNotFoundError(f"Import not found: {p}")
        self._import_stack.add(str(p))
        txt=p.read_text(encoding="utf-8")
        dec=PSONDecoder(txt, custom_types=self.custom_types, base_path=str(p), _import_stack=self._import_stack)
        val=dec.parse()
        self._import_stack.remove(str(p))
        return val
    def _resolve_pointer(self, pointer):
        if not pointer.startswith("#"): pointer="#"+pointer if pointer.startswith("/") else "#"+pointer
        path=pointer[1:]
        if not path or path=="/": return self._root_obj
        parts=[p for p in path.split("/") if p]
        cur=self._root_obj
        for part in parts:
            part=part.replace("~1","/").replace("~0","~")
            if isinstance(cur, dict): cur=cur[part]
            elif isinstance(cur, list): cur=cur[int(part)]
            else: cur=getattr(cur, part)
        return cur
    def _skip(self):
        while self.pos < len(self.text):
            c=self.text[self.pos]
            if c in " \t\r\n": self.pos+=1; continue
            if c=='#':
                while self.pos < len(self.text) and self.text[self.pos]!='\n': self.pos+=1
                continue
            if self.text[self.pos:self.pos+2]=='//':
                while self.pos < len(self.text) and self.text[self.pos]!='\n': self.pos+=1
                continue
            break
    def _parse_value(self):
        self._skip()
        if self.pos>=len(self.text): raise ValueError("EOF")
        c=self.text[self.pos]
        if self.text[self.pos:self.pos+4]=='null': self.pos+=4; return None
        if self.text[self.pos:self.pos+4]=='true': self.pos+=4; return True
        if self.text[self.pos:self.pos+5]=='false': self.pos+=5; return False
        if c in ('"',"'"): return self._parse_string()
        if c=='@': return self._parse_tag()
        if c=='[': return self._parse_list()
        if c=='(': return self._parse_tuple()
        if c=='{': return self._parse_set_or_dict()
        if c.isdigit() or c in '-+': return self._parse_number()
        if c.isalpha() or c in '_$': return self._parse_ident()
        raise ValueError(f"Unexpected {c!r} at {self.pos}")
    def _parse_string(self):
        q=self.text[self.pos]; self.pos+=1; buf=[]
        while self.pos < len(self.text):
            ch=self.text[self.pos]
            if ch=='\\':
                self.pos+=1
                esc=self.text[self.pos] if self.pos < len(self.text) else ''
                m={'n':'\n','t':'\t','r':'\r','\\':'\\','"':'"',"'" :"'"}
                buf.append(m.get(esc,esc)); self.pos+=1
            elif ch==q: self.pos+=1; break
            else: buf.append(ch); self.pos+=1
        return "".join(buf)
    def _parse_number(self):
        s=self.pos
        while self.pos < len(self.text) and self.text[self.pos] in "-+0123456789.eE": self.pos+=1
        tok=self.text[s:self.pos]
        try:
            if '.' in tok or 'e' in tok.lower(): return float(tok)
            return int(tok)
        except Exception: return tok
    def _parse_ident(self):
        s=self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in "_$"): self.pos+=1
        return self.text[s:self.pos]
    def _parse_list(self):
        self.pos+=1; arr=[]; self._skip()
        if self.pos < len(self.text) and self.text[self.pos]==']': self.pos+=1; return arr
        while True:
            self._skip(); arr.append(self._parse_value()); self._skip()
            if self.text[self.pos]==',': self.pos+=1; continue
            if self.text[self.pos]==']': self.pos+=1; break
        return arr
    def _parse_tuple(self):
        self.pos+=1; items=[]; self._skip()
        if self.pos < len(self.text) and self.text[self.pos]==')': self.pos+=1; return tuple(items)
        while True:
            self._skip()
            if self.pos < len(self.text) and self.text[self.pos]==')': self.pos+=1; break
            items.append(self._parse_value()); self._skip()
            if self.text[self.pos]==',': self.pos+=1; self._skip()
            if self.pos < len(self.text) and self.text[self.pos]==')': self.pos+=1; break
        return tuple(items)
    def _parse_set_or_dict(self):
        self.pos+=1; self._skip()
        if self.pos < len(self.text) and self.text[self.pos]=='}': self.pos+=1; return {}
        first=self._parse_value(); self._skip()
        if self.pos < len(self.text) and self.text[self.pos]==':':
            self.pos+=1; self._skip(); val=self._parse_value()
            d={first:val}
            while True:
                self._skip()
                if self.pos>=len(self.text): raise ValueError("unterminated dict")
                if self.text[self.pos]==',': self.pos+=1; self._skip()
                if self.pos < len(self.text) and self.text[self.pos]=='}': self.pos+=1; break
                if self.text[self.pos]=='}': self.pos+=1; break
                k=self._parse_value(); self._skip()
                if self.text[self.pos]!=':': raise ValueError("expected :")
                self.pos+=1; self._skip(); v=self._parse_value(); d[k]=v
            return d
        else:
            s={first}
            while True:
                self._skip()
                if self.pos < len(self.text) and self.text[self.pos]==',': self.pos+=1; self._skip()
                if self.pos < len(self.text) and self.text[self.pos]=='}': self.pos+=1; break
                if self.text[self.pos]=='}': self.pos+=1; break
                s.add(self._parse_value())
            return s
    def _parse_tag(self):
        self.pos+=1
        name=self._parse_ident()
        while self.pos < len(self.text) and self.text[self.pos]=='.': self.pos+=1; name+='.'+self._parse_ident()
        self._skip()
        if self.pos>=len(self.text) or self.text[self.pos]!='(': raise ValueError(f"expected ( after @{name}")
        self.pos+=1; self._skip()
        args=[]; kwargs={}
        if self.pos < len(self.text) and self.text[self.pos]==')': self.pos+=1
        else:
            while True:
                self._skip()
                save=self.pos
                if self.pos < len(self.text) and (self.text[self.pos].isalpha() or self.text[self.pos] in '_$'):
                    ident=self._parse_ident(); self._skip()
                    if self.pos < len(self.text) and self.text[self.pos]=='=':
                        self.pos+=1; self._skip(); v=self._parse_value(); kwargs[ident]=v
                    else:
                        self.pos=save; args.append(self._parse_value())
                else:
                    args.append(self._parse_value())
                self._skip()
                if self.text[self.pos]==',': self.pos+=1; continue
                if self.text[self.pos]==')': self.pos+=1; break
        dotpath=[]
        self._skip()
        while self.pos < len(self.text) and self.text[self.pos]=='.':
            self.pos+=1; dotpath.append(self._parse_ident())
        return self._resolve_tag(name, args, kwargs, dotpath)
    def _resolve_tag(self, name, args, kwargs, dotpath):
        if name=='set':
            if not args: return set()
            if len(args)==1 and isinstance(args[0], (list,set,tuple,frozenset)): return set(args[0])
            return set(args)
        if name=='frozenset':
            if not args: return frozenset()
            if len(args)==1 and isinstance(args[0], (list,set,tuple,frozenset)): return frozenset(args[0])
            return frozenset(args)
        if name=='bytes': return base64.b64decode(args[0]) if args else b""
        if name=='bytearray': return bytearray(base64.b64decode(args[0])) if args else bytearray()
        if name=='datetime': return datetime.datetime.fromisoformat(args[0]) if args else datetime.datetime.now()
        if name=='date': return datetime.date.fromisoformat(args[0]) if args else datetime.date.today()
        if name=='time': return datetime.time.fromisoformat(args[0]) if args else datetime.time()
        if name=='uuid': return uuid.UUID(args[0]) if args else uuid.uuid4()
        if name=='decimal': return decimal.Decimal(args[0]) if args else decimal.Decimal(0)
        if name=='Path': return pathlib.Path(args[0]) if args else pathlib.Path(".")
        if name=='PurePath': return pathlib.PurePath(args[0]) if args else pathlib.PurePath(".")
        if name=='complex': return complex(args[0], args[1]) if len(args)>=2 else complex(args[0]) if args else 0j
        if name=='float':
            m={'nan': float('nan'),'inf': float('inf'),'-inf': float('-inf')}
            if args and args[0] in m: return m[args[0]]
            return float(args[0]) if args else 0.0
        if name=='import':
            path=args[0] if args else ""
            if dotpath: return _ImportRef(path, dotpath)
            return _ImportRef(path, [])
        if name=='ref': return _Ref(args[0] if args else "#/")
        if name=='env': return _Env(args[0] if args else "", kwargs.get("default", args[1] if len(args)>1 else None))
        if name in self.custom_types:
            ctor=self.custom_types[name]
            if isinstance(ctor,type) and issubclass(ctor, Enum):
                if args and isinstance(args[0], str): return ctor[args[0]]
            try:
                if kwargs: return ctor(**kwargs)
                if args and len(args)==1 and isinstance(args[0], dict): return ctor(**args[0])
                return ctor(*args, **kwargs)
            except Exception:
                return {"__pson_tag__": name, "args": args, "kwargs": kwargs}
        return {"__pson_tag__": name, "args": args, "kwargs": kwargs}

# ========= SECURITY (v0.6 compat) =========
class SecurityConfig:
    def __init__(self, max_depth=100, allow_imports=None, max_size=None):
        self.max_depth=max_depth
        self.allow_imports=allow_imports
        self.max_size=max_size

def loads(text, custom_types=None, base_path=None, security=None):
    # security param kept for README compat – currently validated via max_depth check in decoder if needed
    return PSONDecoder(text, custom_types=custom_types, base_path=base_path or ".", security=security).parse()

def load(fp, custom_types=None, security=None):
    base=getattr(fp, 'name', '.')
    return loads(fp.read(), custom_types=custom_types, base_path=base, security=security)

def load_file(path, custom_types=None, security=None):
    p=pathlib.Path(path)
    if p.suffix=='.psonb':
        return loadsb(p.read_bytes(), custom_types=custom_types)
    return loads(p.read_text(encoding='utf-8'), custom_types=custom_types, base_path=str(p), security=security)

def dump(obj, fp, **kw):
    fp.write(dumps(obj, **kw))

# ========= SCHEMA =========
class SchemaError(Exception):
    def __init__(self, path, message, value=None):
        self.path=path; self.message=message; self.value=value
        super().__init__(f"{'.'.join(str(p) for p in path) or 'root'}: {message} (got {value!r})")

class Validator:
    def __init__(self, required=True, default=MISSING, description=None):
        self.required=required; self.default=default; self.description=description
    def validate(self, value, path): raise NotImplementedError

class String(Validator):
    def __init__(self, min_len=None, max_len=None, pattern=None, **kw):
        super().__init__(**kw); self.min_len=min_len; self.max_len=max_len; self.pattern=re.compile(pattern) if pattern else None
    def validate(self, value, path):
        if not isinstance(value, str): raise SchemaError(path, "expected string", value)
        if self.min_len and len(value)<self.min_len: raise SchemaError(path, f"too short min {self.min_len}", value)
        if self.max_len and len(value)>self.max_len: raise SchemaError(path, f"too long max {self.max_len}", value)
        if self.pattern and not self.pattern.search(value): raise SchemaError(path, f"pattern mismatch {self.pattern.pattern}", value)
        return value

class Int(Validator):
    def __init__(self, min=None, max=None, **kw): super().__init__(**kw); self.min=min; self.max=max
    def validate(self, value, path):
        if isinstance(value,bool) or not isinstance(value,int): raise SchemaError(path, "expected int", value)
        if self.min is not None and value<self.min: raise SchemaError(path, f"< min {self.min}", value)
        if self.max is not None and value>self.max: raise SchemaError(path, f"> max {self.max}", value)
        return value

class Float(Validator):
    def __init__(self, min=None, max=None, **kw): super().__init__(**kw); self.min=min; self.max=max
    def validate(self, value, path):
        if isinstance(value,bool) or not isinstance(value,(int,float)): raise SchemaError(path, "expected float", value)
        v=float(value)
        if self.min is not None and v<self.min: raise SchemaError(path, f"< min {self.min}", value)
        if self.max is not None and v>self.max: raise SchemaError(path, f"> max {self.max}", value)
        return v

class Bool(Validator):
    def validate(self, value, path):
        if not isinstance(value,bool): raise SchemaError(path, "expected bool", value)
        return value

class EnumVal(Validator):
    def __init__(self, choices, **kw): super().__init__(**kw); self.choices=set(choices)
    def validate(self, value, path):
        if isinstance(value, Enum): value=value.name
        if value not in self.choices: raise SchemaError(path, f"expected one of {self.choices}", value)
        return value

class ListOf(Validator):
    def __init__(self, of=None, **kw): super().__init__(**kw); self.of=of
    def validate(self, value, path):
        if not isinstance(value,(list,tuple)): raise SchemaError(path, "expected list", value)
        if self.of: return [_validate_value(x, self.of, path+[i]) for i,x in enumerate(value)]
        return list(value)

class SetOf(Validator):
    def __init__(self, of=None, **kw): super().__init__(**kw); self.of=of
    def validate(self, value, path):
        if not isinstance(value,(set,frozenset,list)): raise SchemaError(path, "expected set", value)
        return set(_validate_value(x, self.of, path) if self.of else x for x in value)

class DictOf(Validator):
    def __init__(self, schema=None, **kw): super().__init__(**kw); self.schema=schema
    def validate(self, value, path):
        if not isinstance(value,dict): raise SchemaError(path, "expected dict", value)
        if not self.schema: return value
        out={}
        for k,validator in self.schema.items():
            if k not in value:
                if validator.required:
                    if validator.default is not MISSING: out[k]=validator.default
                    else: raise SchemaError(path, f"missing '{k}'", value)
                else:
                    if validator.default is not MISSING: out[k]=validator.default
            else:
                out[k]=_validate_value(value[k], validator, path+[k])
        for k in set(value.keys())-set(self.schema.keys()):
            out[k]=value[k]
        return out

class Optional(Validator):
    def __init__(self, inner): super().__init__(required=False, default=None); self.inner=inner
    def validate(self, value, path):
        if value is None: return None
        return _validate_value(value, self.inner, path)

class Any(Validator):
    def validate(self, value, path): return value

def _validate_value(value, validator, path):
    if isinstance(validator, Validator): return validator.validate(value, path)
    if isinstance(validator, dict): return DictOf(validator).validate(value, path)
    if isinstance(validator, type) and is_dataclass(validator):
        if isinstance(value, validator): return value
        if not isinstance(value, dict): raise SchemaError(path, f"expected dict for {validator.__name__}", value)
        out={}
        for f in fields(validator):
            if f.name not in value:
                if f.default is not MISSING: out[f.name]=f.default
                elif f.default_factory is not MISSING: out[f.name]=f.default_factory()
                else:
                    origin=get_origin(f.type)
                    if origin is Union and type(None) in get_args(f.type):
                        out[f.name]=None
                    else:
                        raise SchemaError(path, f"missing '{f.name}' for {validator.__name__}", value)
            else:
                out[f.name]=value[f.name]
        return validator(**out)
    return value

def validate(data, schema_def): return _validate_value(data, schema_def, [])

class schema:
    String=String; Int=Int; Float=Float; Bool=Bool; ListOf=ListOf; SetOf=SetOf; DictOf=DictOf; EnumVal=EnumVal; Optional=Optional; Any=Any
    @staticmethod
    def string(**kw): return String(**kw)
    @staticmethod
    def int(**kw): return Int(**kw)
    @staticmethod
    def float(**kw): return Float(**kw)
    @staticmethod
    def bool(): return Bool()
    @staticmethod
    def enum(*c): return EnumVal(c)
    @staticmethod
    def list_of(of=None, **kw): return ListOf(of=of, **kw)
    @staticmethod
    def set_of(of=None, **kw): return SetOf(of=of, **kw)
    @staticmethod
    def dict_of(s=None, **kw): return DictOf(schema=s, **kw)
    @staticmethod
    def optional(inner): return Optional(inner)
    @staticmethod
    def any(): return Any()
    @staticmethod
    def validate(data, schema_def): return validate(data, schema_def)

# ========= BINARY =========
MAGIC=b'PSONB'; VER=5
T_NULL=0; T_FALSE=1; T_TRUE=2
T_INT64=10; T_INT_BIG=11; T_FLOAT64=12; T_COMPLEX=13
T_STRING=20; T_BYTES=21; T_BYTEARRAY=22
T_LIST=30; T_TUPLE=31; T_SET=32; T_DICT=33; T_FROZENSET=34
T_DATETIME=40; T_DATE=41; T_TIME=42; T_UUID=43; T_DECIMAL=44; T_PATH=45; T_PUREPATH=46
T_TENSOR=50; T_CUSTOM=60
DTYPE_MAP={0:'float32',1:'float64',2:'int32',3:'int64',4:'uint8',5:'int8',6:'bool'}
DTYPE_RMAP={v:k for k,v in DTYPE_MAP.items()}

def _w_u32(f,v): f.write(struct.pack('>I', v))
def _w_u64(f,v): f.write(struct.pack('>Q', v))
def _w_u8(f,v): f.write(struct.pack('>B', v))
def _w_i64(f,v): f.write(struct.pack('>q', v))
def _r_u32(f): return struct.unpack('>I', f.read(4))[0]
def _r_u64(f): return struct.unpack('>Q', f.read(8))[0]
def _r_u8(f): return struct.unpack('>B', f.read(1))[0]
def _r_i64(f): return struct.unpack('>q', f.read(8))[0]

def _enc_bin(obj, f):
    if obj is None: _w_u8(f, T_NULL)
    elif obj is False: _w_u8(f, T_FALSE)
    elif obj is True: _w_u8(f, T_TRUE)
    elif isinstance(obj, int) and not isinstance(obj, bool):
        try:
            if -2**63 <= obj < 2**63:
                _w_u8(f, T_INT64); _w_i64(f, obj)
            else: raise OverflowError
        except Exception:
            _w_u8(f, T_INT_BIG)
            s=str(obj).encode(); _w_u32(f, len(s)); f.write(s)
    elif isinstance(obj, float):
        _w_u8(f, T_FLOAT64); f.write(struct.pack('>d', obj))
    elif isinstance(obj, complex):
        _w_u8(f, T_COMPLEX); f.write(struct.pack('>dd', obj.real, obj.imag))
    elif isinstance(obj, str):
        _w_u8(f, T_STRING); b=obj.encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, bytes):
        _w_u8(f, T_BYTES); _w_u64(f, len(obj)); f.write(obj)
    elif isinstance(obj, bytearray):
        _w_u8(f, T_BYTEARRAY); _w_u64(f, len(obj)); f.write(obj)
    elif isinstance(obj, list):
        _w_u8(f, T_LIST); _w_u32(f, len(obj))
        for x in obj: _enc_bin(x, f)
    elif isinstance(obj, tuple):
        _w_u8(f, T_TUPLE); _w_u32(f, len(obj))
        for x in obj: _enc_bin(x, f)
    elif isinstance(obj, set):
        _w_u8(f, T_SET); _w_u32(f, len(obj))
        for x in obj: _enc_bin(x, f)
    elif isinstance(obj, frozenset):
        _w_u8(f, T_FROZENSET); _w_u32(f, len(obj))
        for x in obj: _enc_bin(x, f)
    elif isinstance(obj, dict):
        _w_u8(f, T_DICT); _w_u32(f, len(obj))
        for k,v in obj.items(): _enc_bin(k, f); _enc_bin(v, f)
    elif isinstance(obj, datetime.datetime):
        _w_u8(f, T_DATETIME); b=obj.isoformat().encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, datetime.date) and not isinstance(obj, datetime.datetime):
        _w_u8(f, T_DATE); b=obj.isoformat().encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, datetime.time):
        _w_u8(f, T_TIME); b=obj.isoformat().encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, uuid.UUID):
        _w_u8(f, T_UUID); b=str(obj).encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, decimal.Decimal):
        _w_u8(f, T_DECIMAL); b=str(obj).encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, pathlib.Path):
        _w_u8(f, T_PATH); b=str(obj).encode(); _w_u32(f, len(b)); f.write(b)
    elif isinstance(obj, pathlib.PurePath):
        _w_u8(f, T_PUREPATH); b=str(obj).encode(); _w_u32(f, len(b)); f.write(b)
    else:
        try:
            import numpy as np
            if isinstance(obj, np.ndarray):
                _w_u8(f, T_TENSOR)
                dtype_str=str(obj.dtype)
                if dtype_str not in DTYPE_RMAP:
                    obj=obj.astype('float64'); dtype_str='float64'
                _w_u8(f, DTYPE_RMAP[dtype_str]); _w_u8(f, obj.ndim)
                for d in obj.shape: _w_u32(f, d)
                raw=obj.tobytes(); _w_u64(f, len(raw)); f.write(raw)
                return
        except Exception: pass
        if is_dataclass(obj):
            _w_u8(f, T_CUSTOM); n=obj.__class__.__name__.encode(); _w_u32(f, len(n)); f.write(n); _enc_bin(asdict(obj), f)
        elif isinstance(obj, Enum):
            _w_u8(f, T_CUSTOM); n=obj.__class__.__name__.encode(); _w_u32(f, len(n)); f.write(n); _enc_bin(obj.name, f)
        elif hasattr(obj, '__dict__'):
            _w_u8(f, T_CUSTOM); n=obj.__class__.__name__.encode(); _w_u32(f, len(n)); f.write(n); _enc_bin(obj.__dict__, f)
        else:
            raise TypeError(f"Cannot bin encode {type(obj)}")

def _dec_bin(f):
    t=_r_u8(f)
    if t==T_NULL: return None
    if t==T_FALSE: return False
    if t==T_TRUE: return True
    if t==T_INT64: return _r_i64(f)
    if t==T_INT_BIG: l=_r_u32(f); return int(f.read(l).decode())
    if t==T_FLOAT64: return struct.unpack('>d', f.read(8))[0]
    if t==T_COMPLEX: r,i=struct.unpack('>dd', f.read(16)); return complex(r,i)
    if t==T_STRING: l=_r_u32(f); return f.read(l).decode()
    if t==T_BYTES: l=_r_u64(f); return f.read(l)
    if t==T_BYTEARRAY: l=_r_u64(f); return bytearray(f.read(l))
    if t==T_LIST: c=_r_u32(f); return [_dec_bin(f) for _ in range(c)]
    if t==T_TUPLE: c=_r_u32(f); return tuple(_dec_bin(f) for _ in range(c))
    if t==T_SET: c=_r_u32(f); return set(_dec_bin(f) for _ in range(c))
    if t==T_FROZENSET: c=_r_u32(f); return frozenset(_dec_bin(f) for _ in range(c))
    if t==T_DICT:
        c=_r_u32(f); d={}
        for _ in range(c):
            k=_dec_bin(f); v=_dec_bin(f); d[k]=v
        return d
    if t==T_DATETIME: l=_r_u32(f); return datetime.datetime.fromisoformat(f.read(l).decode())
    if t==T_DATE: l=_r_u32(f); return datetime.date.fromisoformat(f.read(l).decode())
    if t==T_TIME: l=_r_u32(f); return datetime.time.fromisoformat(f.read(l).decode())
    if t==T_UUID: l=_r_u32(f); return uuid.UUID(f.read(l).decode())
    if t==T_DECIMAL: l=_r_u32(f); return decimal.Decimal(f.read(l).decode())
    if t==T_PATH: l=_r_u32(f); return pathlib.Path(f.read(l).decode())
    if t==T_PUREPATH: l=_r_u32(f); return pathlib.PurePath(f.read(l).decode())
    if t==T_TENSOR:
        dcode=_r_u8(f); ndim=_r_u8(f); shape=tuple(_r_u32(f) for _ in range(ndim)); dlen=_r_u64(f); raw=f.read(dlen)
        try:
            import numpy as np
            dtype=DTYPE_MAP.get(dcode,'float64')
            return np.frombuffer(raw, dtype=dtype).reshape(shape).copy()
        except: return {"__tensor__": True, "dtype": DTYPE_MAP.get(dcode), "shape": shape}
    if t==T_CUSTOM:
        l=_r_u32(f); name=f.read(l).decode(); payload=_dec_bin(f)
        if name in _registry:
            ctor=_registry[name]
            if isinstance(ctor, type) and issubclass(ctor, Enum):
                if isinstance(payload, str): return ctor[payload]
            try:
                if isinstance(payload, dict): return ctor(**payload)
                return ctor(payload)
            except Exception: return {"__pson_tag__": name, "payload": payload}
        return {"__pson_tag__": name, "payload": payload}
    raise ValueError(f"Unknown type {t}")

def dumpsb(obj) -> bytes:
    buf=io.BytesIO(); buf.write(MAGIC); buf.write(struct.pack('>B', VER)); _enc_bin(obj, buf); return buf.getvalue()

def loadsb(data: bytes, custom_types=None):
    if custom_types: _registry.update(custom_types)
    buf=io.BytesIO(data)
    magic=buf.read(5)
    if magic!=MAGIC: raise ValueError("Not PSONB")
    ver=struct.unpack('>B', buf.read(1))[0]
    if ver!=VER: raise ValueError(f"Version {ver}")
    return _dec_bin(buf)

def dumpb(obj, fp): fp.write(dumpsb(obj))
def loadb(fp, custom_types=None):
    data=fp.read() if hasattr(fp,'read') else fp
    return loadsb(data, custom_types=custom_types)

def dumpb_stream(objs, fp):
    fp.write(MAGIC); fp.write(struct.pack('>B', VER)); _w_u32(fp, len(objs))
    for obj in objs:
        b=io.BytesIO(); _enc_bin(obj, b); data=b.getvalue()
        _w_u64(fp, len(data)); fp.write(data)

def loadb_stream(fp):
    buf=fp if hasattr(fp,'read') else io.BytesIO(fp)
    magic=buf.read(5)
    if magic!=MAGIC: raise ValueError("Not PSONB stream")
    ver=struct.unpack('>B', buf.read(1))[0]
    count=_r_u32(buf)
    for _ in range(count):
        l=_r_u64(buf); data=buf.read(l)
        yield loadsb(MAGIC+struct.pack('>B', VER)+data)

# ========= CLI =========
def _cli():
    p=argparse.ArgumentParser(prog="pson", description="PSON toolkit v0.6 - one file")
    sub=p.add_subparsers(dest="cmd", required=True)
    fmt=sub.add_parser("fmt", help="Format .pson")
    fmt.add_argument("file"); fmt.add_argument("-i","--inplace", action="store_true"); fmt.add_argument("--indent", type=int, default=2)
    chk=sub.add_parser("check", help="Check valid PSON")
    chk.add_argument("file")
    diff=sub.add_parser("diff", help="Semantic diff")
    diff.add_argument("a"); diff.add_argument("b")
    tj=sub.add_parser("to-json", help="PSON -> JSON")
    tj.add_argument("file"); tj.add_argument("-o","--output")
    fj=sub.add_parser("from-json", help="JSON -> PSON")
    fj.add_argument("file"); fj.add_argument("-o","--output")
    tb=sub.add_parser("to-psonb", help="PSON -> PSONB")
    tb.add_argument("file"); tb.add_argument("-o","--output")
    fb=sub.add_parser("from-psonb", help="PSONB -> PSON")
    fb.add_argument("file"); fb.add_argument("-o","--output"); fb.add_argument("--inspect", action="store_true")
    args=p.parse_args()
    if args.cmd=="fmt":
        path=pathlib.Path(args.file)
        obj=loads(path.read_text(encoding="utf-8"), base_path=str(path))
        out=dumps(obj, indent=args.indent)
        if args.inplace:
            path.write_text(out+"\n", encoding="utf-8")
            print(f"Formatted {args.file}")
        else:
            print(out)
    elif args.cmd=="check":
        try:
            load_file(args.file)
            print(f"OK: {args.file}")
        except Exception as e:
            print(f"FAIL: {e}"); sys.exit(1)
    elif args.cmd=="diff":
        a=load_file(args.a); b=load_file(args.b)
        def diff_d(a,b, path=""):
            diffs=[]
            if isinstance(a,dict) and isinstance(b,dict):
                keys=set(a.keys())|set(b.keys())
                for k in sorted(keys):
                    if k not in a: diffs.append(f"+ {path}.{k}: {b[k]!r}")
                    elif k not in b: diffs.append(f"- {path}.{k}: {a[k]!r}")
                    else:
                        if a[k]!=b[k]:
                            if isinstance(a[k],dict) and isinstance(b[k],dict):
                                diffs.extend(diff_d(a[k], b[k], f"{path}.{k}" if path else k))
                            else:
                                if type(a[k])!=type(b[k]):
                                    diffs.append(f"~ {path}.{k}: type {type(a[k]).__name__} -> {type(b[k]).__name__} | {a[k]!r} -> {b[k]!r}")
                                else:
                                    diffs.append(f"~ {path}.{k}: {a[k]!r} -> {b[k]!r}")
            else:
                if a!=b:
                    diffs.append(f"~ {path}: {a!r} -> {b!r}")
            return diffs
        diffs=diff_d(a,b)
        if not diffs: print("No differences")
        else:
            for d in diffs: print(d)
    elif args.cmd=="to-json":
        obj=load_file(args.file)
        def jd(o):
            import pathlib, uuid, decimal, datetime
            from enum import Enum
            from dataclasses import is_dataclass, asdict
            if isinstance(o,(set,frozenset,tuple)): return list(o)
            if isinstance(o,(datetime.datetime, datetime.date, datetime.time)): return o.isoformat()
            if isinstance(o,pathlib.Path): return str(o)
            if isinstance(o,uuid.UUID): return str(o)
            if isinstance(o,decimal.Decimal): return str(o)
            if isinstance(o,bytes): return o.hex()
            if isinstance(o,Enum): return o.name
            if is_dataclass(o): return asdict(o)
            try:
                import numpy as np
                if isinstance(o,np.ndarray): return o.tolist()
            except Exception: pass
            return str(o)
        j=json.dumps(obj, default=jd, indent=2)
        if args.output: pathlib.Path(args.output).write_text(j); print(f"Wrote {args.output}")
        else: print(j)
    elif args.cmd=="from-json":
        obj=json.loads(pathlib.Path(args.file).read_text())
        out=dumps(obj, indent=2)
        if args.output: pathlib.Path(args.output).write_text(out); print(f"Wrote {args.output}")
        else: print(out)
    elif args.cmd=="to-psonb":
        obj=load_file(args.file)
        data=dumpsb(obj)
        out=args.output or args.file.replace(".pson",".psonb")
        pathlib.Path(out).write_bytes(data)
        print(f"Wrote {out} {len(data)} bytes")
    elif args.cmd=="from-psonb":
        data=pathlib.Path(args.file).read_bytes()
        obj=loadsb(data)
        if args.inspect:
            print(f"Type {type(obj).__name__} preview {str(obj)[:500]}")
        else:
            out=dumps(obj, indent=2)
            if args.output: pathlib.Path(args.output).write_text(out); print(f"Wrote {args.output}")
            else: print(out)

if __name__=="__main__":
    _cli()
