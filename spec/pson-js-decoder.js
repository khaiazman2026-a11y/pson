/**
 * PSON JS Decoder - Reference Implementation v0.8
 * For spec freeze: proves language-agnostic
 * Supports text .pson (subset) -> JS objects with type preservation
 */

class PSON {
  static parse(text, options = {}) {
    const decoder = new PSONDecoder(text, options);
    return decoder.parse();
  }

  // JS helpers for type distinction
  static isTuple(v) { return v && v.__pson_type === 'tuple'; }
  static isSet(v) { return v instanceof Set; }
  static tuple(...items) { return { __pson_type: 'tuple', items }; }
}

class PSONDecoder {
  constructor(text, options) {
    this.text = text;
    this.pos = 0;
    this.customTypes = options.customTypes || {};
    this.allowImport = options.allowImport || false; // JS version denies import by default for security
  }

  parse() {
    this.skip();
    const val = this.parseValue();
    this.skip();
    return val;
  }

  skip() {
    while (this.pos < this.text.length) {
      const c = this.text[this.pos];
      if (c === ' ' || c === '\t' || c === '\n' || c === '\r') { this.pos++; continue; }
      if (c === '#') { while (this.pos < this.text.length && this.text[this.pos] !== '\n') this.pos++; continue; }
      if (this.text.substr(this.pos,2) === '//') { while (this.pos < this.text.length && this.text[this.pos] !== '\n') this.pos++; continue; }
      break;
    }
  }

  parseValue() {
    this.skip();
    if (this.pos >= this.text.length) throw new Error("EOF");
    const c = this.text[this.pos];
    if (this.text.substr(this.pos,4) === 'null') { this.pos+=4; return null; }
    if (this.text.substr(this.pos,4) === 'true') { this.pos+=4; return true; }
    if (this.text.substr(this.pos,5) === 'false') { this.pos+=5; return false; }
    if (c === '"' || c === "'") return this.parseString();
    if (c === '@') return this.parseTag();
    if (c === '[') return this.parseList();
    if (c === '(') return this.parseTuple();
    if (c === '{') return this.parseSetOrDict();
    if ((c >= '0' && c <= '9') || c === '-' || c === '+') return this.parseNumber();
    if (/[A-Za-z_$]/.test(c)) return this.parseIdent();
    throw new Error(`Unexpected ${c} at ${this.pos}`);
  }

  parseString() {
    const q = this.text[this.pos]; this.pos++;
    let buf = "";
    while (this.pos < this.text.length) {
      const ch = this.text[this.pos];
      if (ch === '\\') {
        this.pos++;
        const esc = this.text[this.pos] || "";
        const map = { n: "\n", t: "\t", r: "\r", "\\": "\\", '"': '"', "'": "'" };
        buf += map[esc] || esc;
        this.pos++;
      } else if (ch === q) { this.pos++; break; }
      else { buf += ch; this.pos++; }
    }
    return buf;
  }

  parseNumber() {
    const start = this.pos;
    while (this.pos < this.text.length && /[-+0-9.eE]/.test(this.text[this.pos])) this.pos++;
    const tok = this.text.slice(start, this.pos);
    if (tok.includes('.') || tok.toLowerCase().includes('e')) return parseFloat(tok);
    const n = parseInt(tok, 10);
    return isNaN(n) ? tok : n;
  }

  parseIdent() {
    const start = this.pos;
    while (this.pos < this.text.length && /[A-Za-z0-9_$]/.test(this.text[this.pos])) this.pos++;
    return this.text.slice(start, this.pos);
  }

  parseList() {
    this.pos++; this.skip();
    const arr = [];
    if (this.text[this.pos] === ']') { this.pos++; return arr; }
    while (true) {
      this.skip();
      arr.push(this.parseValue());
      this.skip();
      if (this.text[this.pos] === ',') { this.pos++; continue; }
      if (this.text[this.pos] === ']') { this.pos++; break; }
    }
    return arr;
  }

  parseTuple() {
    this.pos++; this.skip();
    const items = [];
    if (this.text[this.pos] === ')') { this.pos++; return { __pson_type: 'tuple', items }; }
    while (true) {
      this.skip();
      if (this.text[this.pos] === ')') { this.pos++; break; }
      items.push(this.parseValue());
      this.skip();
      if (this.text[this.pos] === ',') { this.pos++; this.skip(); if (this.text[this.pos] === ')') { this.pos++; break; } continue; }
      if (this.text[this.pos] === ')') { this.pos++; break; }
    }
    return { __pson_type: 'tuple', items };
  }

  parseSetOrDict() {
    this.pos++; this.skip();
    if (this.text[this.pos] === '}') { this.pos++; return {}; }
    const first = this.parseValue();
    this.skip();
    if (this.text[this.pos] === ':') {
      this.pos++; this.skip();
      const val = this.parseValue();
      const obj = {}; obj[first] = val;
      while (true) {
        this.skip();
        if (this.text[this.pos] === ',') { this.pos++; this.skip(); }
        if (this.text[this.pos] === '}') { this.pos++; break; }
        const k = this.parseValue(); this.skip();
        if (this.text[this.pos] !== ':') throw new Error("expected :");
        this.pos++; this.skip();
        const v = this.parseValue();
        obj[k] = v;
      }
      return obj;
    } else {
      const s = new Set(); s.add(first);
      while (true) {
        this.skip();
        if (this.text[this.pos] === ',') { this.pos++; this.skip(); }
        if (this.text[this.pos] === '}') { this.pos++; break; }
        s.add(this.parseValue());
      }
      return s;
    }
  }

  parseTag() {
    this.pos++; // @
    const name = this.parseIdent();
    this.skip();
    if (this.text[this.pos] !== '(') throw new Error(`expected ( after @${name}`);
    this.pos++; this.skip();
    const args = []; const kwargs = {};
    if (this.text[this.pos] === ')') { this.pos++; }
    else {
      while (true) {
        this.skip();
        const save = this.pos;
        if (/[A-Za-z_$]/.test(this.text[this.pos] || "")) {
          const ident = this.parseIdent(); this.skip();
          if (this.text[this.pos] === '=') { this.pos++; this.skip(); const v = this.parseValue(); kwargs[ident] = v; }
          else { this.pos = save; args.push(this.parseValue()); }
        } else { args.push(this.parseValue()); }
        this.skip();
        if (this.text[this.pos] === ',') { this.pos++; continue; }
        if (this.text[this.pos] === ')') { this.pos++; break; }
      }
    }
    // resolve builtins
    if (name === 'set') { return new Set(args.length===1 && Array.isArray(args[0]) ? args[0] : args); }
    if (name === 'frozenset') { return new Set(args); }
    if (name === 'bytes') { return args[0] || ""; }
    if (name === 'Path' || name === 'PurePath') { return args[0] || ""; }
    if (name === 'datetime' || name === 'date' || name === 'time' || name === 'uuid' || name === 'decimal') { return args[0] || ""; }
    if (name === 'float') { const m={'nan':NaN,'inf':Infinity,'-inf':-Infinity}; return m[args[0]] ?? parseFloat(args[0]); }
    if (name === 'complex') { return { re: args[0], im: args[1] }; }
    if (name === 'import' || name === 'ref' || name === 'env') { return { __pson_tag: name, args, kwargs }; }
    if (this.customTypes[name]) { return this.customTypes[name](...args); }
    return { __pson_tag: name, args, kwargs };
  }
}

// Export for Node / browser
if (typeof module !== 'undefined' && module.exports) module.exports = { PSON, PSONDecoder };
if (typeof window !== 'undefined') window.PSON = PSON;

// Simple self-test
if (typeof require !== 'undefined' && require.main === module) {
  const text = `
  {
    model: "resnet",
    batch: 32,
    coords: (1, 2, 3),
    tags: {a, b, c},
    path: @Path("/tmp"),
    set_val: @set(1,2,3)
  }
  `;
  const obj = PSON.parse(text);
  console.log("Parsed:", obj);
  console.log("coords is tuple?", obj.coords.__pson_type === 'tuple');
  console.log("tags is Set?", obj.tags instanceof Set);
}
