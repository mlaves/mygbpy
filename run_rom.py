import argparse
from cpu import CPU
from memory import Memory

def main():
    parser = argparse.ArgumentParser(description='Run a Game Boy ROM')
    parser.add_argument('rom_file', help='Path to the ROM file to run')

    args = parser.parse_args()

    with open(args.rom_file, "rb") as f:
        rom = f.read()

    cpu = CPU(Memory(rom))

    while not cpu.halted:
        cpu.step()

if __name__ == "__main__":
    main()
