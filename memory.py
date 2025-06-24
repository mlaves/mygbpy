from abc import ABC, abstractmethod

class MBC(ABC):
    @abstractmethod
    def read(self, address: int) -> int:
        pass

    @abstractmethod
    def write(self, address: int, value: int) -> None:
        pass

class NoMBC(MBC):
    def __init__(self, rom: bytes) -> None:
        self.rom = rom

    def read(self, address: int) -> int:
        return self.rom[address]

    def write(self, address: int, value: int) -> None:
        pass  # ROM is read-only; no bank switching

class MBC1(MBC):
    def __init__(self, rom: bytes) -> None:
        self.rom = rom
        self.rom_bank = 0x01

    def read(self, address: int) -> int:
        if address < 0x4000:
            return self.rom[address]
        else:
            return self.rom[address - 0x4000 + self.rom_bank * 0x4000]

    def write(self, address: int, value: int) -> None:
        if 0x2000 <= address <= 0x3FFF:
            value = value & 0b11111  # select lower 5 bits of bank number
            self.rom_bank = value or 0x01

def detect_mbc(rom: bytes) -> MBC:
    mbc_type = rom[0x0147]
    if mbc_type == 0x00:
        return NoMBC(rom)
    elif mbc_type in (0x01, 0x02, 0x03):
        return MBC1(rom)
    else:
        raise NotImplementedError(f"MBC type 0x{mbc_type:02X} not implemented")

class Memory:
    def __init__(self, rom: bytes) -> None:
        self.mbc = detect_mbc(rom)  # 16 KiB ROM bank 00 and 16 KiB ROM bank 01–NN
        self.vram = bytearray(0x2000)  # 8 KiB Video RAM (VRAM)
        self.eram = bytearray(0x2000)  # 8 KiB External RAM (ERAM)
        self.wram = bytearray(0x2000)  # 8 KiB Work RAM (WRAM)
        self.oam = bytearray(0xA0)  # 160 bytes Object Attribute Memory (OAM)
        self.io = bytearray(0x80)  # 128 bytes I/O Registers
        self.hram = bytearray(0x7F)  # 127 bytes High RAM (HRAM)
        self.ie_register = 0x00  # Interrupt Enable Register

    def __getitem__(self, address: int) -> int:
        return self.read(address)

    def __setitem__(self, address: int, value: int) -> None:
        self.write(address, value)

    def read(self, address: int) -> int:
        if 0x0000 <= address <= 0x7FFF:
            return self.mbc.read(address)
        elif 0x8000 <= address <= 0x9FFF:
            return self.vram[address - 0x8000]
        elif 0xA000 <= address <= 0xBFFF:
            return self.eram[address - 0xA000]
        elif 0xC000 <= address <= 0xCFFF:
            return self.wram[address - 0xC000]
        elif 0xD000 <= address <= 0xDFFF:
            return self.wram[0x1000 + (address - 0xD000)]
        elif 0xE000 <= address <= 0xFDFF:
            # Echo RAM (mirror of C000-DDFF)
            return self.read(address - 0x2000)
        elif 0xFE00 <= address <= 0xFE9F:
            return self.oam[address - 0xFE00]
        elif 0xFEA0 <= address <= 0xFEFF:
            # Unusable area
            return 0x00
        elif 0xFF00 <= address <= 0xFF7F:
            return self.io[address - 0xFF00]
        elif 0xFF80 <= address <= 0xFFFE:
            return self.hram[address - 0xFF80]
        elif address == 0xFFFF:
            return self.ie_register
        else:
            # Invalid/unmapped memory
            raise ValueError(f"Invalid memory address: 0x{address:04X}")

    def write(self, address: int, value: int):
        value = value & 0xFF  # ensure value is 8 bits

        if 0x0000 <= address <= 0x7FFF:
            # writing to MBC triggers MBC logic (bank switching, etc.)
            self.mbc.write(address, value)
        elif 0x8000 <= address <= 0x9FFF:
            self.vram[address - 0x8000] = value
        elif 0xA000 <= address <= 0xBFFF:
            self.eram[address - 0xA000] = value
        elif 0xC000 <= address <= 0xCFFF:
            self.wram[address - 0xC000] = value
        elif 0xD000 <= address <= 0xDFFF:
            self.wram[0x1000 + (address - 0xD000)] = value
        elif 0xE000 <= address <= 0xFDFF:
            # Echo RAM (mirror of C000-DDFF)
            self.write(address - 0x2000, value)
        elif 0xFE00 <= address <= 0xFE9F:
            self.oam[address - 0xFE00] = value
        elif 0xFEA0 <= address <= 0xFEFF:
            # Unusable area
            raise ValueError(f"Cannot write to unusable memory: 0x{address:04X}")
        elif 0xFF00 <= address <= 0xFF7F:
            self.io[address - 0xFF00] = value
            # TODO: handle IO registers
        elif 0xFF80 <= address <= 0xFFFE:
            self.hram[address - 0xFF80] = value
        else:
            # Invalid/unmapped memory
            raise ValueError(f"Invalid memory address: 0x{address:04X}")
