from cpu import CPU
from memory import Memory

with open("06-ld r,r.gb", "rb") as f:
    rom = f.read()

cpu = CPU(Memory(rom))

while not cpu.halted:
    cpu.step()
