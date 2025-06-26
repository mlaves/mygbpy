from typing import Callable

from memory import Memory


class Instruction:
    def __init__(self, name: str, opcode: int, length: int, cycles: int, description: str, handler: Callable):
        self.name = name
        self.opcode = opcode
        self.length = length
        self.cycles = cycles
        self.description = description
        self.handler = handler

    def __str__(self):
        return f"{self.name} (0x{self.opcode:02X})"


class CPU:
    """
    CPU class for the Game Boy.

    This class implements the Game Boy's CPU, which is a Sharp SM83 processor.
    It is responsible for executing instructions and managing the CPU's state.

    The Game Boy CPU is little-endian. This means that when multi-byte values are stored in memory, the least
    significant byte is stored at the lower memory address and the most significant byte is stored at the higher memory
    address.
    """

    def __init__(self, memory: Memory) -> None:
        self.memory = memory
        self._pc = 0x0100  # Start execution here
        self._sp = 0xFFFE  # Stack pointer (top of stack)

        # 8-bit registers (internal storage)
        self._a = 0x01
        self._f = 0x00  # Flags: Z N H C (bit 7 to bit 4)
        self._b = self._c = self._d = self._e = self._h = self._l = 0x00

        self.halted = False
        self.instructions = self.build_instruction_table()

    def step(self):
        if self.halted:
            return 0  # No cycles consumed when halted

        opcode = self.memory[self.pc]
        self.pc += 1
        self.pc &= 0xFFFF

        instruction = self.instructions.get(
            opcode, Instruction("not implemented", 0, 0, 0, "", self.instr_unimplemented)
        )
        cycles = instruction.cycles
        instruction.handler()

        return cycles

    # --- PC Property ---

    @property
    def pc(self) -> int:
        """16-bit Program Counter"""
        return self._pc

    @pc.setter
    def pc(self, value: int) -> None:
        """Set PC with automatic 16-bit wrapping"""
        self._pc = value & 0xFFFF

    # --- SP Property ---

    @property
    def sp(self) -> int:
        """16-bit Stack Pointer"""
        return self._sp

    @sp.setter
    def sp(self, value: int) -> None:
        """Set SP with automatic 16-bit wrapping"""
        self._sp = value & 0xFFFF

    # --- 8-bit Register Properties ---

    @property
    def a(self) -> int:
        """8-bit accumulator register"""
        return self._a

    @a.setter
    def a(self, value: int) -> None:
        self._a = value & 0xFF

    @property
    def f(self) -> int:
        """8-bit flags register (only bits 4-7 are used)"""
        return self._f

    @f.setter
    def f(self, value: int) -> None:
        self._f = value & 0xF0  # Only lower 4 bits are used for flags

    @property
    def b(self) -> int:
        """8-bit B register"""
        return self._b

    @b.setter
    def b(self, value: int) -> None:
        self._b = value & 0xFF

    @property
    def c(self) -> int:
        """8-bit C register"""
        return self._c

    @c.setter
    def c(self, value: int) -> None:
        self._c = value & 0xFF

    @property
    def d(self) -> int:
        """8-bit D register"""
        return self._d

    @d.setter
    def d(self, value: int) -> None:
        self._d = value & 0xFF

    @property
    def e(self) -> int:
        """8-bit E register"""
        return self._e

    @e.setter
    def e(self, value: int) -> None:
        self._e = value & 0xFF

    @property
    def h(self) -> int:
        """8-bit H register"""
        return self._h

    @h.setter
    def h(self, value: int) -> None:
        self._h = value & 0xFF

    @property
    def l(self) -> int:
        """8-bit L register"""
        return self._l

    @l.setter
    def l(self, value: int) -> None:
        self._l = value & 0xFF

    # --- Flag Handling Methods ---

    def _set_flags(
        self, zero: bool = None, subtract: bool = None, half_carry: bool = None, carry: bool = None
    ) -> None:
        """Set flags based on operation result and conditions"""
        flags = 0

        # Z flag (bit 7) - set if result is zero
        if zero is not None:
            flags |= (1 if zero else 0) << 7

        # N flag (bit 6) - set if operation was subtraction
        if subtract is not None:
            flags |= (1 if subtract else 0) << 6

        # H flag (bit 5) - set if there was half carry/borrow
        if half_carry is not None:
            flags |= (1 if half_carry else 0) << 5

        # C flag (bit 4) - set if there was carry/borrow
        if carry is not None:
            flags |= (1 if carry else 0) << 4

        # Preserve existing flags that weren't explicitly set
        mask = 0
        if zero is not None:
            mask |= 0x80
        if subtract is not None:
            mask |= 0x40
        if half_carry is not None:
            mask |= 0x20
        if carry is not None:
            mask |= 0x10

        # Clear the bits we're setting, preserve the others
        self._f = (self._f & ~mask) | (flags & mask)

    def _check_half_carry_sub(self, a: int, b: int) -> bool:
        """Check for half carry in subtraction (borrow from bit 4)"""
        return (a & 0x0F) < (b & 0x0F)

    def _check_half_carry_add(self, a: int, b: int) -> bool:
        """Check for half carry in addition (carry to bit 4)"""
        return ((a & 0x0F) + (b & 0x0F)) > 0x0F

    def print_registers(self):
        print(f"AF: {self.af:04X}")
        print(f"BC: {self.bc:04X}")
        print(f"DE: {self.de:04X}")
        print(f"HL: {self.hl:04X}")
        print(f"SP: {self.sp:04X}")
        print(f"PC: {self.pc:04X}")

    def print_flags(self):
        print("Z N H C")
        print(
            f"{int(self.f & 0x80 != 0)} {int(self.f & 0x40 != 0)} {int(self.f & 0x20 != 0)} {int(self.f & 0x10 != 0)}"
        )

    # --- 16-bit Register Properties ---

    @property
    def af(self) -> int:
        """16-bit AF register (A << 8 | F)"""
        return (self.a << 8) | self.f

    @af.setter
    def af(self, value: int) -> None:
        value = value & 0xFFFF
        self.a = value >> 8
        self.f = value & 0xF0  # Only lower 4 bits of F are used for flags

    @property
    def bc(self) -> int:
        """16-bit BC register (B << 8 | C)"""
        return (self.b << 8) | self.c

    @bc.setter
    def bc(self, value: int) -> None:
        value = value & 0xFFFF
        self.b = value >> 8
        self.c = value & 0xFF

    @property
    def de(self) -> int:
        """16-bit DE register (D << 8 | E)"""
        return (self.d << 8) | self.e

    @de.setter
    def de(self, value: int) -> None:
        value = value & 0xFFFF
        self.d = value >> 8
        self.e = value & 0xFF

    @property
    def hl(self) -> int:
        """16-bit HL register (H << 8 | L)"""
        return (self.h << 8) | self.l

    @hl.setter
    def hl(self, value: int) -> None:
        value = value & 0xFFFF
        self.h = value >> 8
        self.l = value & 0xFF

    def build_instruction_table(self):
        return {
            0x00: Instruction(
                "NOP",
                0x00,
                1,
                1,
                "Only advances the program counter by 1. Performs no other operations that would have an effect.",
                self.instr_NOP,
            ),
            0x01: Instruction(
                "LD BC, d16",
                0x01,
                3,
                3,
                "Load the 2 bytes of immediate data into register pair BC.",
                self.instr_LD_BC_d16,
            ),
            0x02: Instruction(
                "LD (BC), A",
                0x02,
                1,
                2,
                "Store the contents of register A in the memory location specified by register pair BC.",
                self.instr_LD_BC_A,
            ),
            0x03: Instruction(
                "INC BC", 0x03, 1, 2, "Increment the contents of register pair BC by 1.", self.instr_INC_BC
            ),
            0x04: Instruction("INC B", 0x04, 1, 1, "Increment the contents of register B by 1.", self.instr_INC_B),
            0x05: Instruction("DEC B", 0x05, 1, 1, "Decrement the contents of register B by 1.", self.instr_DEC_B),
            0x06: Instruction(
                "LD B, d8", 0x06, 2, 2, "Load the 8-bit immediate operand d8 into register B.", self.instr_LD_B_d8
            ),
            0x07: Instruction("RLCA", 0x07, 1, 1, "Rotate register A left through carry flag.", self.instr_RLCA),
            0x08: Instruction(
                "LD (a16), SP",
                0x08,
                3,
                5,
                "Store the lower byte of stack pointer SP at the address specified by the 16-bit immediate operand a16, and store the upper byte of SP at address a16 + 1.",
                self.instr_LD_a16_SP
            ),
            0x09: Instruction(
                "ADD HL, BC",
                0x09,
                1,
                2,
                "Add the contents of register pair BC to the contents of register pair HL, and store the results in register pair HL.",
                self.instr_ADD_HL_BC
            ),
            0x0A: Instruction(
                "LD A, (BC)",
                0x0A,
                1,
                2,
                "Load the 8-bit contents of memory specified by register pair BC into register A.",
                self.instr_LD_A_BC
            ),
            0x0B: Instruction(
                "DEC BC",
                0x0B,
                1,
                2,
                "Decrement the contents of register pair BC by 1.",
                self.instr_DEC_BC
            ),
            0x0C: Instruction(
                "INC C",
                0x0C,
                1,
                1,
                "Increment the contents of register C by 1.",
                self.instr_INC_C
            ),
            0x0D: Instruction(
                "DEC C",
                0x0D,
                1,
                1,
                "Decrement the contents of register C by 1.",
                self.instr_DEC_C
            ),
            0x0E: Instruction(
                "LD C, d8",
                0x0E,
                2,
                2,
                "Load the 8-bit immediate operand d8 into register C.",
                self.instr_LD_C_d8
            ),
            0x0F: Instruction(
                "RRCA",
                0x0F,
                1,
                1,
                "Rotate the contents of register A to the right.",
                self.instr_RRCA
            ),
            0x10: Instruction(
                "STOP",
                0x10,
                2,
                1,
                "Execution of a STOP instruction stops both the system clock and oscillator circuit.",
                self.instr_STOP
            ),
            0x11: Instruction(
                "LD DE, d16",
                0x11,
                3,
                3,
                "Load the 2 bytes of immediate data into register pair DE.",
                self.instr_LD_DE_d16
            ),
            0x12: Instruction(
                "LD (DE), A",
                0x12,
                1,
                2,
                "Store the contents of register A in the memory location specified by register pair DE.",
                self.instr_LD_DE_A
            ),
            0x13: Instruction(
                "INC DE",
                0x13,
                1,
                2,
                "Increment the contents of register pair DE by 1.",
                self.instr_INC_DE
            ),
            0x14: Instruction(
                "INC D",
                0x14,
                1,
                1,
                "Increment the contents of register D by 1.",
                self.instr_INC_D
            ),
            0x15: Instruction(
                "DEC D",
                0x15,
                1,
                1,
                "Decrement the contents of register D by 1.",
                self.instr_DEC_D
            ),
            0x16: Instruction(
                "LD D, d8",
                0x16,
                2,
                2,
                "Load the 8-bit immediate operand d8 into register D.",
                self.instr_LD_D_d8

            ),
            0x17: Instruction(
                "RLA",
                0x17,
                1,
                1,
                "Rotate the contents of register A to the left, through the carry (CY) flag.",
                self.instr_RLA
            ),
            0x18: Instruction(
                "JR s8",
                0x18,
                2,
                3,
                "Jump s8 steps from the current address in the program counter (PC).",
                self.instr_JR_s8
            ),
            0x19: Instruction(
                "ADD HL, DE",
                0x19,
                1,
                2,
                "Add the contents of register pair DE to the contents of register pair HL, and store the results in register pair HL.",
                self.instr_ADD_HL_DE
            ),
            0x1A: Instruction(
                "LD A, (DE)",
                0x1A,
                1,
                2,
                "Load the 8-bit contents of memory specified by register pair DE into register A.",
                self.instr_LD_A_DE
            ),
            0x1B: Instruction(
                "DEC DE",
                0x1B,
                1,
                2,
                "Decrement the contents of register pair DE by 1.",
                self.instr_DEC_DE
            ),
            0x1C: Instruction(
                "INC E",
                0x1C,
                1,
                1,
                "Increment the contents of register E by 1.",
                self.instr_INC_E
            ),
            0x1D: Instruction(
                "DEC E",
                0x1D,
                1,
                1,
                "Decrement the contents of register E by 1.",
                self.instr_DEC_E
            ),
            0x1E: Instruction(
                "LD E, d8",
                0x01E,
                2,
                2,
                "Load the 8-bit immediate operand d8 into register E.",
                self.instr_LD_E_d8
            ),
            0x21: Instruction(
                "LD HL, d16",
                0x21,
                3,
                3,
                "Load the 2 bytes of immediate data into register pair HL.",
                self.instr_LD_HL_d16

            ),
            0x3E: Instruction(
                "LD A, d8",
                0x3E,
                2,
                2,
                "Load the 8-bit immediate operand d8 into register A.",
                self.instr_LD_A_d8,
            ),
            0x47: Instruction(
                "LD B, A",
                0x47,
                1,
                1,
                "Load the contents of register A into register B.",
                self.instr_LD_B_A,
            ),
            0x76: Instruction("HALT", 0x76, 1, 1, "Halt the CPU", self.instr_HALT),
            0x78: Instruction(
                "LD A, B",
                0x78,
                1,
                1,
                "Load the contents of register B into register A.",
                self.instr_LD_A_B,
            ),
            0xC3: Instruction(
                "JP d16",
                0xC3,
                3,
                4,
                "Load the 16-bit immediate operand a16 into the program counter (PC).",
                self.instr_JP_d16,
            ),
            # 0xFF
        }

    def instr_unimplemented(self):
        opcode = self.memory[self.pc - 1]
        raise NotImplementedError(f"Opcode 0x{opcode:02X} not implemented")

    # --- Instruction Implementations ---

    def instr_NOP(self):
        # 0x00
        pass

    def instr_LD_BC_d16(self):
        # 0x01
        self.c = self.memory[self.pc]
        self.b = self.memory[self.pc + 1]
        self.pc += 2

    def instr_LD_BC_A(self):
        # 0x02
        self.memory[self.bc] = self.a

    def instr_INC_BC(self):
        # 0x03
        self.bc = self.bc + 1

    def instr_INC_B(self):
        # 0x04
        old_value = self.b
        self.b += 1
        self._set_flags(zero=self.b == 0, half_carry=self._check_half_carry_add(old_value, 1))

    def instr_DEC_B(self):
        # 0x05
        old_value = self.b
        self.b -= 1
        self._set_flags(zero=self.b == 0, half_carry=self._check_half_carry_sub(old_value, 1), subtract=True)

    def instr_LD_B_d8(self):
        # 0x06
        self.b = self.memory[self.pc]
        self.pc += 1

    def instr_RLCA(self):
        # 0x07
        old_value = self.a
        self.a = ((self.a << 1) | (self.a >> 7)) & 0xFF
        self._set_flags(zero=False, subtract=False, half_carry=False, carry=(old_value & 0x80) != 0)

    def instr_LD_a16_SP(self):
        # 0x08
        pointer = self.memory[self.pc] | (self.memory[self.pc+1] << 8)
        self.memory[pointer] = self.sp & 0x00FF  # Lower byte of SP
        self.memory[pointer + 1] = (self.sp >> 8) & 0x00FF  # Upper byte of SP
        self.pc += 2

    def instr_ADD_HL_BC(self):
        # 0x09
        old_hl = self.hl
        result = old_hl + self.bc

        # Store result (automatically wrapped to 16 bits by property setter)
        self.hl = result

        # Set flags: Z is unchanged, N=0, H=half_carry, C=carry
        self._set_flags(subtract=False, half_carry=((old_hl & 0x0FFF) + (self.bc & 0x0FFF)) > 0x0FFF, carry=result > 0xFFFF)

    def instr_LD_A_BC(self):
        # 0x0A
        self.a = self.memory[self.bc]

    def instr_DEC_BC(self):
        # 0x0B
        self.bc -= 1

    def instr_INC_C(self):
        # 0x0C
        old_value = self.c
        self.c += 1
        self._set_flags(zero=self.c == 0, subtract=False, half_carry=self._check_half_carry_add(old_value, 1))

    def instr_DEC_C(self):
        # 0x0D
        old_value = self.c
        self.c -= 1
        self._set_flags(zero=self.c == 0, subtract=True, half_carry=self._check_half_carry_sub(old_value, 1))

    def instr_LD_C_d8(self):
        # 0x0E
        self.c = self.memory[self.pc]
        self.pc += 1

    def instr_RRCA(self):
        # 0x0F
        old_value = self.a
        self.a = ((self.a >> 1) | (self.a << 7)) & 0xFF
        self._set_flags(zero=False, subtract=False, half_carry=False, carry=(old_value & 0x01) != 0)

    def instr_STOP(self):
        # 0x10
        # STOP is not used in any licensed ROM and therefore implemented as NOP here.
        self.pc += 1

    def instr_LD_DE_d16(self):
        # 0x11
        self.de = self.memory[self.pc] | (self.memory[self.pc+1] << 8)
        self.pc += 2

    def instr_LD_DE_A(self):
        # 0x12
        self.memory[self.de] = self.a

    def instr_INC_DE(self):
        # 0x13
        self.de += 1

    def instr_INC_D(self):
        # 0x14
        old_value = self.d
        self.d += 1
        self._set_flags(zero=self.d == 0, subtract=False, half_carry=self._check_half_carry_add(old_value, 1))

    def instr_DEC_D(self):
        # 0x15
        old_value = self.d
        self.d -= 1
        self._set_flags(zero=self.d == 0, subtract=True, half_carry=self._check_half_carry_sub(old_value, 1))

    def instr_LD_D_d8(self):
        # 0x16
        self.d = self.memory[self.pc]

    def instr_RLA(self):
        # 0x17
        old_value = self.a
        self.a = ((self.a << 1) | ((self.f & 0x10) >> 4)) & 0xFF
        self._set_flags(zero=False, subtract=False, half_carry=False, carry=(old_value & 0x80) > 0)

    def instr_JR_s8(self):
        # 0x18
        s8 = self.memory[self.pc]
        self.pc += 1  # Move PC to point after the instruction

        # Using two's complement conversion
        if s8 >= 0x80:  # If bit 7 is set (negative number)
            s8 -= 0x100  # Shift from [0, 255] to [-128, 127]
        self.pc += s8

    def instr_ADD_HL_DE(self):
        # 0x19
        old_value = self.hl
        new_value = self.hl + self.de
        self.hl = new_value
        self._set_flags(
            subtract=False,
            half_carry=((old_value & 0x0FFF) + (self.de & 0x0FFF)) > 0x0FFF,  # set if overflow from bit 11
            carry=new_value > 0xFFFF  # set if overflow from bit 15
        )

    def instr_LD_A_DE(self):
        # 0x1A
        self.a = self.memory[self.de]

    def instr_DEC_DE(self):
        # 0x1B
        self.de -= 1

    def instr_INC_E(self):
        # 0x1C
        old_value = self.e
        self.e += 1
        self._set_flags(zero=self.e == 0, subtract=False, half_carry=self._check_half_carry_add(old_value, 1))

    def instr_DEC_E(self):
        # 0x1D
        old_value = self.e
        self.e -= 1
        self._set_flags(zero=self.e == 0, subtract=True, half_carry=self._check_half_carry_sub(old_value, 1))

    def instr_LD_E_d8(self):
        # 0x1E
        self.e = self.memory[self.pc]
        self.pc += 1

    def instr_LD_HL_d16(self):
        # 0x21
        self.hl = self.memory[self.pc] | (self.memory[self.pc+1] << 8)
        self.pc += 2

    def instr_LD_B_A(self):
        # 0x47
        self.b = self.a

    def instr_HALT(self):
        # 0x76
        self.halted = True

    def instr_LD_A_B(self):
        # 0x78
        self.a = self.b

    def instr_LD_A_d8(self):
        # 0x3E
        self.a = self.memory[self.pc]
        self.pc += 1

    def instr_JP_d16(self):
        # 0xC3
        value = self.memory[self.pc] | (self.memory[self.pc+1] << 8)
        self.pc = value
