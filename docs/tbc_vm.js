// Tiny Bytecode VM (browser-friendly JavaScript)
// Follows the same instruction set and semantics as the Python reference:
// - No integer literals (numeric tokens throw an error)
// - Single-char opcodes: + - * / @ ! & ; > < ? . , ^
// - Labels: :name define a label, $name pushes label address
// - Comments start with # to end of line; whitespace is ignored

class TinyBytecodeVM {
  constructor() {
    this.dataStack = [];
    this.returnStack = [];
    this.memory = Object.create(null);
    this.labels = {};
    this.instructions = [];

    // Hooks
    this.onOutput = (ch) => { /* default: no-op */ };
    this.onRead = async () => { return -1; /* EOF by default */ };
  }

  push(v) { this.dataStack.push(Number(v)); }
  pop() {
    if (this.dataStack.length === 0) throw new Error('Data stack underflow');
    return this.dataStack.pop();
  }
  rpop() {
    if (this.returnStack.length === 0) throw new Error('Return stack underflow');
    return this.returnStack.pop();
  }

  loadProgram(text) {
    // remove comments (from # to end of line) and split tokens
    const lines = text.split(/\r?\n/).map(l => l.split('#',1)[0]);
    const raw = lines.join(' ');
    const tokens = raw.split(/\s+/).filter(t => t.length > 0);

    // first pass: register labels and collect instructions
    const instrs = [];
    const labels = Object.create(null);
    let pc = 0;
    for (const tok of tokens) {
      if (tok.startsWith(':')) {
        const name = tok.slice(1);
        if (!name) throw new Error('Empty label name');
        labels[name] = pc;
      } else {
        instrs.push(tok);
        pc += 1;
      }
    }

    // resolve $name to @ADDR:n pseudo-token
    const resolved = instrs.map(tok => {
      if (tok.startsWith('$')) {
        const name = tok.slice(1);
        if (!(name in labels)) throw new Error('Unknown label referenced: ' + name);
        return '@ADDR:' + labels[name];
      }
      return tok;
    });

    this.instructions = resolved;
    this.labels = labels;
  }

  async step(ip) {
    if (ip < 0 || ip >= this.instructions.length) return { nextIp: null, halted: true };
    const tok = this.instructions[ip];

    // numeric tokens are not allowed
    if (/^[+-]?\d+$/.test(tok)) {
      throw new Error(`Integer-Literale sind nicht Teil der VM-Spezifikation: '${tok}' (ip=${ip})`);
    }

    if (tok.startsWith('@ADDR:')) {
      const addr = Number(tok.split(':',2)[1]);
      this.push(addr);
      return { nextIp: null, halted: false };
    }

    // single-char ops
    switch (tok) {
      case '+': { const a = this.pop(); const b = this.pop(); this.push(b + a); return { nextIp: null, halted: false }; }
      case '-': { const a = this.pop(); const b = this.pop(); this.push(b - a); return { nextIp: null, halted: false }; }
      case '*': { const a = this.pop(); this.push(a << 1); return { nextIp: null, halted: false }; }
      case '/': { const a = this.pop(); this.push(a >> 1); return { nextIp: null, halted: false }; }
      case '@': { const addr = this.pop(); this.push(this.memory[Number(addr)] || 0); return { nextIp: null, halted: false }; }
      case '!': { const val = this.pop(); const addr = this.pop(); this.memory[Number(addr)] = Number(val); return { nextIp: null, halted: false }; }
      case '&': { const addr = this.pop(); this.returnStack.push(ip + 1); return { nextIp: Number(addr), halted: false }; }
      case ';': { const ret = this.rpop(); return { nextIp: Number(ret), halted: false }; }
      case '>': { const v = this.pop(); this.returnStack.push(v); return { nextIp: null, halted: false }; }
      case '<': { const v = this.rpop(); this.push(v); return { nextIp: null, halted: false }; }
      case '?': { const addr = this.pop(); const cond = this.pop(); if (cond > 0) return { nextIp: Number(addr), halted: false }; return { nextIp: null, halted: false }; }
      case '^': { return { nextIp: null, halted: true }; }
      case '.': { const v = this.pop(); const ch = String.fromCharCode(Number(v) & 0xFF); try { this.onOutput(ch); } catch (e) {}; return { nextIp: null, halted: false }; }
      case ',': {
        // onRead can be async; default returns -1
        const r = await this.onRead();
        if (typeof r === 'number') this.push(r & 0xFF);
        else if (r === null || r === undefined) this.push(-1);
        else this.push(Number(r) & 0xFF);
        return { nextIp: null, halted: false };
      }
      default:
        throw new Error(`Unknown token/instruction: ${tok} at ip=${ip}`);
    }
  }

  // run until halt or maxSteps; returns a Promise that resolves when finished
  async run(maxSteps = 100000) {
    let ip = 0;
    let steps = 0;
    while (steps < maxSteps) {
      const { nextIp, halted } = await this.step(ip);
      if (halted) break;
      if (nextIp === null) ip += 1; else ip = nextIp;
      steps += 1;
    }
    if (steps >= maxSteps) throw new Error('Step limit exceeded');
  }

  async runText(text, maxSteps = 100000) {
    this.loadProgram(text);
    await this.run(maxSteps);
  }
}

// Export for browser global
if (typeof window !== 'undefined') window.TinyBytecodeVM = TinyBytecodeVM;
if (typeof module !== 'undefined' && module.exports) module.exports = TinyBytecodeVM;
