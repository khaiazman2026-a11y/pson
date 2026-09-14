"""
flask-pson: PSON integration for Flask + Jinja
Built from Android Termux, Ipoh
"""
import pathlib, sys

# Add project root to path so we can find PSON_ALL_IN_ONE.py
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import PSON_ALL_IN_ONE as pson
except ImportError:
    # fallback if installed via pip
    try:
        import pson
    except ImportError:
        import importlib.util
        p = ROOT / "PSON_ALL_IN_ONE.py"
        spec = importlib.util.spec_from_file_location("pson", p)
        pson = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pson)

def init_pson(app, path="config.pson", jinja_filter=True):
    p = pathlib.Path(path)
    # if relative, resolve from caller or from app root
    if not p.is_absolute():
        # try integration/flask folder first, then root
        cand1 = pathlib.Path(__file__).parent / path
        cand2 = ROOT / path
        if cand1.exists():
            p = cand1
        elif cand2.exists():
            p = cand2
    
    if not p.exists():
        app.logger.warning(f"[flask-pson] {p} not found, skipping")
        return {}
    
    cfg = pson.load_file(str(p))
    if isinstance(cfg, dict):
        app.config.update(cfg)
    
    if jinja_filter:
        app.jinja_env.filters['pson'] = pson.dumps
        app.jinja_env.filters['psonb'] = lambda x: pson.dumps(x)
    
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['pson'] = cfg
    return cfg

def jsonify_pson(*args, **kwargs):
    from flask import Response
    if args and kwargs:
        raise TypeError("jsonify_pson() behavior undefined")
    if len(args) == 1:
        data = args[0]
    else:
        data = args or kwargs
    body = pson.dumps(data)
    return Response(body, mimetype="application/pson")

