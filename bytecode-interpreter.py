import msvcrt
import sys
import locale
import os

# Ermitteln der aktuellen Codepage
# codepage = locale.getpreferredencoding()
codepage = "cp850"
    
# Definition der getch-Funktion
def getch():
    """Wartet auf einen Tastendruck und gibt das Zeichen zurück."""
    if os.name == 'nt':  # Windows-spezifischer Teil
        import msvcrt
        return msvcrt.getch().decode(codepage)
    
    # Unix-spezifischer Teil (Linux, macOS)
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class Byterpret:
    def __init__(self):
        self.mem=bytearray(30000)
        self.pc = 0x400
        self.dstack=0x100
        self.dptr = 0
        self.rstack=0x180
        self.rptr = 0
        self.varadr = 0x0300
        self.result = ""
        self.debug = False
        self.showsrc = False
        self.command_list = [
            ('+', self.add),
            ('-', self.sub),
            ('>', self.shift_right),
            ('<', self.shift_left), 
            ('?', self.branch), # conditional jump
            ('&', self.call), # call
            (';', self.ret),  # return
            (':', self.label), # label
            ('@', self.fetch),
            ('!', self.store),
            ('#', self.comment), # comment
            ('$', self.find), # find
            ('.', self.emit), # emit
            (',', self.get) # getch
        ]

    def dpush8(self, v):
        self.mem[self.dstack+self.dptr] = v & 0xff
        self.dptr += 1

    def dpop8(self):
        self.dptr -= 1
        if self.dptr < 0:
            print("Stack underflow!")
            exit()
        return self.mem[self.dstack+self.dptr]

    def dpush16(self, v):
        self.dpush8(v)
        self.dpush8(v>>8)

    def dpop16(self):
        v = self.dpop8()
        v = v << 8
        v |= self.dpop8()
        return v
        
    def rpush8(self, v):
        self.mem[self.rstack+self.rptr] = v&0xff
        self.rptr += 1

    def rpop8(self):
        self.rptr -= 1
        return self.mem[self.rstack+self.rptr]

    def rpush16(self, v):
        self.rpush8(v)
        self.rpush8(v>>8)

    def rpop16(self):
        v = self.rpop8()
        v = v << 8
        v |= self.rpop8()
        return v

    def fetch16(self):
        adr = self.dpop16()        
        self.dpush8(self.mem[adr] & 0xff)
        self.dpush8(self.mem[adr+1] & 0xff)

    def store8(self,v,adr):
        self.mem[adr] = v & 0xff
        
    def store16(self, v, adr):
        vL = v & 0xff
        vH = (v >> 8) & 0xff 
        self.store8(vL, adr)
        self.store8(vH, adr+1)
        if self.debug:
            print(f"after store: {v} {vL} {vH} {adr}")

    # commands for interpreter

    def add(self): # '+'
        v2 = self.dpop16()
        v1 = self.dpop16()
        self.dpush16((v1+v2) & 0xffff) 

    def sub(self): # '-'
        v2 = self.dpop16()
        v1 = self.dpop16()
        self.dpush16((v1-v2) & 0xffff)

    def shift_right(self): # '>'
        v = self.dpop16()
        self.dpush16(v//2)

    def shift_left(self): # '<'
        v = self.dpop16()
        self.dpush16( (v*2) & 0xffff )

    def branch(self): # '?'
        gt = self.dpop16()
        r = self.dpop16()
        if r > 0 and r & 0x8000 == 0:
            self.pc = gt - 1 # In der Interpreterschleife wird automatisch 1 zu self.pc addiert

    def call(self): # '&' : jump to subroutine
        self.rpush16(self.pc)
        self.pc = self.dpop16()-1 # In der Interpreterschleife wird automatisch 1 zu self.pc addiert

    def ret(self): # ';' : # return from subroutine 
        self.pc = self.rpop16()

    def label(self): # ':'
        self.pc += 1
        
    def fetch(self): # '@':
        self.fetch16()

    def store(self): # '!':
        adr = self.dpop16()
        v   = self.dpop16()
        self.store16(v, adr)

    def comment(self): # '#'
        while self.c != '\n':
            self.c = self.readchar()

    def find(self): # '$'
        v = self.readchar()
        a = self.pc
        self.c = self.readchar()
        found = False
        while not found:
            if self.c == '#':
                self.c = self.readchar()
                while self.c != '\n':
                    self.c = self.readchar()
            elif self.c == ':':
                self.c = self.readchar()
                if self.c == v:
                    found = True
            else:
                self.c = self.readchar()
        self.dpush16(self.pc+1) # die Folgeadresse
        self.pc = a

    def emit(self): # '.'
        v = self.dpop16() & 0xff
        self.result += chr(v)
        print(chr(v), end="", flush=True)

    def get(self): # ','
        v = ( ord(getch()) & 0xff )
        self.dpush16(v)
        print(chr(v), end="", flush=True)

    def getvaradr(self, vname):
        if vname < 'a' or vname > 'z':
            print(f"unknown variable: {vname} at address {self.adr}")
        return self.varadr + 2 * (ord(vname) - ord('a'))

    def pushvaradr(self, c):
            a = self.getvaradr(c)
            self.dpush16(a)
    
    def load(self, address=0x1000, filename="test.bp", strip_comments=False):
        self.pc = address
        self.address = address
        with open(filename,'r') as file:
            for line in file:
                if strip_comments:
                    i = line.find('#')
                    if i >= 0:
                        line = line[0:i]
                    line = line.strip()
                    if line and line[0] != ':':
                        line = line.replace(' ', '')
                for c in line:
                    self.mem[self.pc] = ord(c)
                    self.pc += 1
        if self.showsrc:
            for c in range(address, self.pc):
                print(chr(self.mem[c]),end="", flush=True)
            print("",flush=True)

    def readchar(self):
        self.pc += 1
        c = chr(self.mem[self.pc])
        if self.debug:
            pass
            # print("..readchar: ", c)
        return c

    def interpret(self, adr):
        self.pc = adr
        self.c = chr(self.mem[self.pc])
        while self.c != '^':
            if self.pc < self.address or self.pc > 0x9500:
                print()
                print("Emergency BREAK!")
                break
            self.execute()
            self.c = self.readchar()
        print()
        if self.debug:
            print(f"result: {self.result}")
        
    def execute(self):
        if self.debug:
            print("...execute: ", self.c, hex(self.pc), self.mem[self.pc])
            print("....dstack: ", end="")
            for x in range(0,self.dptr):
                print(self.mem[self.dstack + x],end="")
                print(",",end="")
            print()

            print("....rstack: ", end="")
            for x in range(0,self.rptr):
                print(self.mem[self.rstack + x],end="")
                print(",",end="")
            print()

        if self.c >= 'a' and self.c <= 'z':
            self.pushvaradr(self.c)

        else:
            func = next((t[1] for t in self.command_list if t[0] == self.c), None)
            if func != None:
                func()
            
if __name__ == '__main__':
    bp = Byterpret()
    file = "test.bp"
    stripit = True
    addr = 0x1000
    if len(sys.argv)>1:
        file = sys.argv[1]
    if "-showsrc" in sys.argv:
        bp.showsrc = True
    if "-debug" in sys.argv:
        bp.debug = True
    if "-nostrip" in sys.argv:
        stripit = False
    if "-address" in sys.argv:
        i = sys.argv.index("-address")
        i = i+1
        if i<len(sys.argv):
            addr = int(sys.argv[i], 0)
    
    bp.load(address=addr, filename=file, strip_comments=stripit)
    bp.interpret(addr)
    
