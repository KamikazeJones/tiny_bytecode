"""Tiny Bytecode (TBC) Interpreter

Annäherung an die in `README.md` beschriebene Instruktionsmenge.

Integer-Literale sind nicht Teil der Sprache.

- "+" ist binär: pop b, pop a -> push (a + b).
- "-" ist binär: pop b, pop a -> push (a - b).
- "." gibt das oberste Stack-Element als ASCII-Zeichen aus (nur die unteren 8 Bit).
- "," liest ein Byte/Zeichen von stdin und legt dessen Wert (0-255) auf den Stack;
    bei EOF wird -1 abgelegt.
- "^" beendet das Programm sofort (Halt-Opcode).
- "#" ist das Kommentarzeichen: alles nach `#` bis zum Zeilenende wird ignoriert.
- "*" verdoppelt (einfaches left-shift): pop a -> push (a << 1).
- "/" halbiert (right-shift): pop a -> push (a >> 1).
- "@" dereferenziert: pop addr -> push memory.get(addr, 0).
- "!" schreibt: pop value, pop addr -> memory[addr] = value.
- "&" call: pop addr -> push return-ip auf Return-Stack, set ip=addr.
- ";" return: pop return-ip von Return-Stack und set ip=return-ip.
- ">": pop value von Data-Stack und push auf Return-Stack.
- "<": pop value von Return-Stack und push auf Data-Stack.
- "?": pop addr, pop cond -> falls cond>0 set ip=addr (bedingter Sprung).
- "$name" drückt die Adresse des Labels `:name` auf den Data-Stack.
- ":name" definiert ein Label (entfernt aus der Instruktionssequenz).

Diese Implementation trifft vernünftige Entscheidungen bei Unklarheiten
und dokumentiert sie oben. Wenn Du andere Semantiken möchtest, sag Bescheid
— ich passe die Implementierung an.
"""
from __future__ import annotations

from typing import List, Dict, Tuple, Optional
import sys


class TinyBytecodeVM:
    def __init__(self):
        self.data_stack: List[int] = []
        self.return_stack: List[int] = []
        self.memory: Dict[int, int] = {}
        self.labels: Dict[str, int] = {}
        self.instructions: List[str] = []

    def push(self, v: int) -> None:
        self.data_stack.append(int(v))

    def pop(self) -> int:
        if not self.data_stack:
            raise IndexError("Data stack underflow")
        return self.data_stack.pop()

    def rpop(self) -> int:
        if not self.return_stack:
            raise IndexError("Return stack underflow")
        return self.return_stack.pop()

    def load_program(self, text: str) -> None:
        # Remove comments (from # to end-of-line) and split tokens
        lines = [line.split('#', 1)[0] for line in text.splitlines()]
        raw = " ".join(lines)
        tokens = [tok for tok in raw.split() if tok != ""]

        # First pass: register labels (:name) and build instruction list without labels
        instrs: List[str] = []
        labels: Dict[str, int] = {}
        pc = 0
        for tok in tokens:
            if tok.startswith(":"):
                name = tok[1:]
                if name == "":
                    raise ValueError("Empty label name")
                labels[name] = pc
            else:
                instrs.append(tok)
                pc += 1

        # Resolve $name to a PUSH_ADDR pseudo-token like "@ADDR:n"
        resolved: List[str] = []
        for tok in instrs:
            if tok.startswith("$"):
                name = tok[1:]
                if name not in labels:
                    raise ValueError(f"Unknown label referenced: {name}")
                resolved.append(f"@ADDR:{labels[name]}")
            else:
                resolved.append(tok)

        self.instructions = resolved
        self.labels = labels

    def step(self, ip: int) -> Tuple[Optional[int], bool]:
        """Execute one instruction at ip. Returns (next_ip, halted).
        If next_ip is None the VM will advance to ip+1.
        """
        if ip < 0 or ip >= len(self.instructions):
            return None, True

        tok = self.instructions[ip]

        # Integer-Literale sind gemäß Spezifikation nicht erlaubt.
        # Falls ein numerisches Token auftaucht, geben wir einen klaren Fehler aus.
        if tok.lstrip("-+").isdigit():
            raise ValueError(
                f"Integer-Literale sind nicht Teil der VM-Spezifikation: '{tok}' (ip={ip})"
            )

        # resolved address push
        if tok.startswith("@ADDR:"):
            addr = int(tok.split(":", 1)[1])
            self.push(addr)
            return None, False

        # Single-char opcodes
        if tok == "+":
            a = self.pop(); b = self.pop(); self.push(b + a); return None, False
        if tok == "-":
            a = self.pop(); b = self.pop(); self.push(b - a); return None, False
        if tok == "*":
            a = self.pop(); self.push(a << 1); return None, False
        if tok == "/":
            a = self.pop(); self.push(a >> 1); return None, False
        if tok == "@":
            addr = self.pop(); self.push(self.memory.get(addr, 0)); return None, False
        if tok == "!":
            val = self.pop(); addr = self.pop(); self.memory[int(addr)] = int(val); return None, False
        if tok == "&":
            addr = self.pop();
            # push return address (next instruction index) on return stack
            self.return_stack.append(ip + 1)
            # jump to addr
            return int(addr), False
        if tok == ";":
            ret = self.rpop();
            return int(ret), False
        if tok == ">":
            v = self.pop(); self.return_stack.append(v); return None, False
        if tok == "<":
            v = self.rpop(); self.push(v); return None, False
        if tok == "?":
            addr = self.pop(); cond = self.pop();
            if cond > 0:
                return int(addr), False
            return None, False

        # Halt-Opcode: beendet die Ausführung sofort
        if tok == "^":
            return None, True

        # Ausgabe eines ASCII-Zeichens (nur untere 8 Bit)
        if tok == ".":
            v = self.pop()
            ch = chr(int(v) & 0xFF)
            sys.stdout.write(ch)
            sys.stdout.flush()
            return None, False

        # Ein Zeichen von stdin lesen und als Zahl (0-255) auf den Stack legen.
        # Bei EOF legen wir -1 auf den Stack.
        if tok == ",":
            ch = sys.stdin.read(1)
            if ch == "":
                self.push(-1)
            else:
                self.push(ord(ch[0]) & 0xFF)
            return None, False

        raise ValueError(f"Unknown token/instruction: {tok} at ip={ip}")

    def run(self, max_steps: int = 100000) -> None:
        ip = 0
        steps = 0
        while steps < max_steps:
            next_ip, halted = self.step(ip)
            if halted:
                break
            if next_ip is None:
                ip += 1
            else:
                ip = next_ip
            steps += 1
        if steps >= max_steps:
            raise RuntimeError("Step limit exceeded")

    def run_text(self, text: str, max_steps: int = 100000) -> None:
        self.load_program(text)
        self.run(max_steps=max_steps)


def run_file(path: str) -> TinyBytecodeVM:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    vm = TinyBytecodeVM()
    vm.run_text(text)
    return vm


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <file.tbc>")
        sys.exit(2)
    vm = run_file(sys.argv[1])
    print("Data stack:", vm.data_stack)
    print("Return stack:", vm.return_stack)
    print("Memory:", vm.memory)
