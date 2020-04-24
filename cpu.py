"""CPU functionality."""

import sys

## ALU ops
ADD = 0b10100000
SUB = 0b10100001
MUL = 0b10100010
DIV = 0b10100011
MOD = 0b10100100
INC = 0b01100101
DEC = 0b01100110
CMP = 0b10100111
AND = 0b10101000
NOT = 0b01101001
OR  = 0b10101010
XOR = 0b10101011
SHL = 0b10101100
SHR = 0b10101101

## PC mutators
CALL = 0b01010000
RET  = 0b00010001
INT  = 0b01010010
IRET = 0b00010011
JMP  = 0b01010100
JEQ  = 0b01010101
JNE  = 0b01010110
JGT  = 0b01010111
JLT  = 0b01011000
JLE  = 0b01011001
JGE  = 0b01011010

## Other
NOP  = 0b00000000
HLT  = 0b00000001
LDI  = 0b10000010
LD   = 0b10000011
ST   = 0b10000100
PUSH = 0b01000101
POP  = 0b01000110
PRN  = 0b01000111
PRA  = 0b01001000

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.pc = 0 # Program Counter, address of the currently executing instruction
        self.ram = [0] * 256  # 256 bytes of memory (RAM)
        self.register = [0] * 8  # 8 general-purpose CPU registers
        self.register[7] = 0xF4 # R7 is the SP
        self.flag = 0b00000000
        self.running = True

        self.branch_table = {
          LDI: self.ldi,
          PRN: self.prn,
          MUL: "MUL",
          ADD: "ADD",
          CMP: "CMP",
          PUSH: self.push,
          POP: self.pop,
          CALL: self.call,
          RET: self.ret,
          JMP: self.jmp,
          JEQ: self.jeq,
          JNE: self.jne
        }


    def ram_read(self, address):
      return self.ram[address]

    def ram_write(self, address, value):
      self.ram[address] = value

    def load(self, filename):
        """Load a program into memory."""

        address = 0

        with open(filename, 'r') as f:
            for line in f.readlines():
                line = line.split('#')[0].strip()
                if line.startswith(('0', '1')) and len(line) == 8:
                    instruction = int(line, 2)
                    self.ram_write(address, instruction)
                    address += 1


    def alu(self, op, register_a, register_b):
        """ALU operations."""

        if op == ADD:
            self.register[register_a] += self.register[register_b]
        elif op == MUL:
          self.register[register_a] *= self.register[register_b]
        elif op == CMP:
          if self.register[register_a] == self.register[register_b]:
            self.flag = 0b00000001
          elif self.register[register_a] > self.register[register_b]:
            self.flag = 0b00000010
          else:
            self.flag = 0b00000100
        else:
            raise Exception("Unsupported ALU operation")


    def ldi(self):
      """ Set the value of a register to an integer. """
      reg_number = self.ram_read(self.pc + 1)
      value = self.ram_read(self.pc + 2)

      self.register[reg_number] = value

    def prn(self):
      """ Print numeric value stored in the given register. """
      reg_number = self.ram_read(self.pc + 1)
      print(self.register[reg_number])

    def push(self):
      """ Push the value in the given register on the stack. """
      self.register[7] -= 1
      self.ram_write(self.register[7], self.register[self.ram_read(self.pc + 1)])
      self.pc = self.pc + 2
      reg_number = self.ram_read(self.pc + 1)
      self.ram_write(self.register[7], self.register[reg_number])

    def pop(self):
      """ Pop the value at the top of the stack into the given register. """
      self.register[self.ram_read(self.pc + 1)] = self.ram_read(self.register[7])
      self.register[7] += 1
      self.pc = self.pc + 2

    def jmp(self):
      """ Jump to the address stored in the given register. """
      reg_number = self.ram_read(self.pc + 1)
      self.pc = self.register[reg_number]

    def jeq(self):
      """ If equal flag is set (true), jump to the address stored in the given register. """
      reg_number = self.ram_read(self.pc + 1)
      equal = self.flag & 0b00000001
      if equal:
        self.pc = self.register[reg_number]
      else:
        self.pc += 2

    def jne(self):
      """ If E flag is clear (false, 0), jump to the address stored in the given register. """
      reg_number = self.ram_read(self.pc + 1)
      equal = self.flag & 0b00000001
      if not equal:
        self.pc = self.register[reg_number]
      else:
        self.pc += 2

    def call(self, reg_number, value):
      """ Calls a subroutine (function) at the address stored in the register. """
      self.register[7] -= 1
      sp = self.register[7]
      self.ram_write(value, sp)

      value = self.register[reg_number]

    def ret(self):
      """ Return from subroutine. """
      sp = self.register[7]
      self.pc = self.ram_read(sp)
      self.register[7] += 1

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""

        while self.running:
          ir = self.ram_read(self.pc) # Instruction Register, contains a copy of the currently executing instruction
          inst_len = (ir >> 6) + 0b1
          is_ALU = (ir & 0b00100000) >> 5

          register_a = self.ram_read(self.pc+1)
          register_b = self.ram_read(self.pc+2)

          if is_ALU:
            self.alu(ir, register_a, register_b)
            self.pc += inst_len

          elif ir in self.branch_table:
            self.branch_table[ir]()
            self.pc += inst_len

          elif ir == HLT: # Halt
            self.running = False

          else:
            print(f"Invalid instructions {ir}")
            break

