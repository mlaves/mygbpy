from cpu import CPU
from memory import Memory


def setup_cpu_with_instructions(instructions: list[int], start_addr: int = 0x0100) -> CPU:
    """Helper to create a CPU with specific instructions in memory"""
    rom = bytearray(0x7FFF)  # 32 KiB ROM
    for i, instruction in enumerate(instructions):
        rom[start_addr + i] = instruction
    return CPU(Memory(rom))

def test_memory_regions():
    """Test that different memory regions work correctly"""
    rom = bytearray(0x7FFF)  # 32 KiB ROM
    memory = Memory(rom)

    # Test internal RAM
    memory.write(0xC000, 0x42)
    assert memory.read(0xC000) == 0x42, "Internal RAM write/read failed"

    # Test echo RAM
    memory.write(0xE000, 0x84)
    assert memory.read(0xE000) == 0x84, "Echo RAM write/read failed"
    assert memory.read(0xC000) == 0x84, "Echo RAM mirror failed"

    # Test high RAM
    memory.write(0xFF80, 0xAA)
    assert memory.read(0xFF80) == 0xAA, "High RAM write/read failed"

    # Test unusable memory
    try:
        memory.write(0xFEA0, 0x00)
        assert False, "Writing to unusable memory should have raised ValueError"
    except ValueError:
        pass

    # Test invalid memory address
    try:
        memory.read(0xFFFFF)
        assert False, "Reading from invalid memory address should have raised ValueError"
    except ValueError:
        pass

    # Test I/O area
    memory.write(0xFF00, 0x55)
    assert memory.read(0xFF00) == 0x55, "I/O area write/read failed"

def test_nop():
    cpu = setup_cpu_with_instructions([0x00])
    cpu.step()
    assert cpu.pc == 0x0101, "test_nop failed"

def test_ld_bc_d16():
    cpu = setup_cpu_with_instructions([0x01, 0x39, 0x30])
    cpu.step()
    assert cpu.bc == 0x3039, "test_ld_bc_d16 failed"

def test_ld_bc_a():
    cpu = setup_cpu_with_instructions([0x02])
    cpu.a = 0xFF
    cpu.bc = 0xC000
    cpu.step()
    assert cpu.memory.read(0xC000) == 0xFF, "test_ld_bc_a failed"

def test_inc_bc():
    cpu = setup_cpu_with_instructions([0x03])
    cpu.bc = 0xC000
    cpu.step()
    assert cpu.bc == 0xC001, "test_inc_bc failed"

def test_inc_b():
    cpu = setup_cpu_with_instructions([0x04])
    cpu.b = 0xFF
    cpu.step()
    assert cpu.b == 0x00, "test_inc_b failed"
    assert cpu.f == 0xA0, "test_inc_b failed"

def test_dec_b():
    cpu = setup_cpu_with_instructions([0x05, 0x05])
    cpu.b = 0xFF
    cpu.step()
    assert cpu.b == 0xFE, "test_dec_b failed"
    assert cpu.f == 0x40, "test_dec_b failed"
    cpu.b = 0x00
    cpu.step()
    assert cpu.b == 0xFF, "test_dec_b failed"
    assert cpu.f == 0x60, "test_dec_b failed"

def test_ld_b_d8():
    cpu = setup_cpu_with_instructions([0x06, 0xFF])
    cpu.step()
    assert cpu.b == 0xFF, "test_ld_b_d8 failed"

def test_ld_a_bc():
    cpu = setup_cpu_with_instructions([0x0A])
    cpu.memory.write(0xC000, 0xFF)
    cpu.bc = 0xC000
    cpu.step()
    assert cpu.a == 0xFF, "test_ld_a_bc failed"

def test_ld_b_a():
    cpu = setup_cpu_with_instructions([0x47])
    cpu.a = 0xFF
    cpu.step()
    assert cpu.b == 0xFF, "test_ld_b_a failed"

def test_halt():
    cpu = setup_cpu_with_instructions([0x76])
    cpu.step()
    assert cpu.halted, "test_halt failed"

def test_ld_a_b():
    cpu = setup_cpu_with_instructions([0x78])
    cpu.b = 0xFF
    cpu.step()
    assert cpu.a == 0xFF, "test_ld_a_b failed"

def test_ld_a_d8():
    cpu = setup_cpu_with_instructions([0x3E, 0xFF])
    cpu.step()
    assert cpu.a == 0xFF, "test_ld_a_d8 failed"

def test_jp_d16():
    cpu = setup_cpu_with_instructions([0xC3, 0x96, 0x00])
    cpu.step()
    assert cpu.pc == 0x0096, "test_jp_d16 failed"

def test_rlca():
    # Test RLCA with bit 7 set
    cpu = setup_cpu_with_instructions([0x07])
    cpu.a = 0x80  # 10000000
    cpu.step()
    assert cpu.a == 0x01, "test_rlca failed: rotation incorrect"
    assert cpu.f == 0x10, "test_rlca failed: carry flag not set"  # Only C flag should be set

    # Test RLCA with bit 7 clear
    cpu = setup_cpu_with_instructions([0x07])
    cpu.a = 0x40  # 01000000
    cpu.step()
    assert cpu.a == 0x80, "test_rlca failed: rotation incorrect"
    assert cpu.f == 0x00, "test_rlca failed: flags not reset"  # All flags should be 0

    # Test RLCA with all bits set
    cpu = setup_cpu_with_instructions([0x07])
    cpu.a = 0xFF  # 11111111
    cpu.step()
    assert cpu.a == 0xFF, "test_rlca failed: rotation incorrect"
    assert cpu.f == 0x10, "test_rlca failed: carry flag not set"  # Only C flag should be set

def test_inc_c():
    cpu = setup_cpu_with_instructions([0x0C, 0x0C, 0x0C])  # INC C
    cpu.c = 0x00
    cpu.step()
    assert cpu.c == 0x01, "test_inc_c failed: result incorrect"
    assert cpu.f == 0x00, "test_inc_c failed: flags not set"  # All flags should be 0

    cpu.c = 0x0F
    cpu.step()
    assert cpu.c == 0x10, "test_inc_c failed: result incorrect"
    assert cpu.f == 0x20, "test_inc_c failed: flags not set"  # Only H flag should be set

    cpu.c = 0xFF
    cpu.step()
    assert cpu.c == 0x00, "test_inc_c failed: result incorrect"
    assert cpu.f == 0xA0, "test_inc_c failed: flags not set"  # Z and H flags should be set

def test_ld_hl_d16():
    cpu = setup_cpu_with_instructions([0x21, 0x34, 0x12])  # LD HL, d16
    cpu.step()
    assert cpu.hl == 0x1234, "test_ld_hl_d16: result incorrect"

def test_add_hl_bc():
    cpu = setup_cpu_with_instructions([0x09, 0x09, 0x09])  # ADD HL, BC
    cpu.hl = 0x1234
    cpu.bc = 0x4321
    cpu.step()
    assert cpu.hl == 0x1234 + 0x4321, "test_add_hl_bc failed: incorrect result"

    # check for 11th bit overflow flag
    cpu.hl = 0x0FFE
    cpu.bc = 0x0002
    cpu.step()
    assert cpu.hl == 0x0FFE + 0x0002, "test_add_hl_bc failed: incorrect result"
    assert cpu.f == 0x20, "test_add_hl_bc failed: half carray flag incorrect"

    # check for 15th bit overflow flag
    cpu.hl = 0xC000
    cpu.bc = 0x8000
    cpu.step()
    assert cpu.hl == ((0xC000 + 0x8000) & 0xFFFF), "test_add_hl_bc failed: incorrect result"
    assert cpu.f != 0x20, "test_add_hl_bc failed: half carray flag incorrect"
    assert cpu.f == 0x10, "test_add_hl_bc failed: carray flag incorrect"

def test_ld_a16_sp():
    cpu = setup_cpu_with_instructions([0x08, 0x00, 0xC0])  # LD (0xC000), SP
    cpu.sp = 0x1234  # Set stack pointer to a known value
    cpu.step()

    # Check that the lower byte (0x34) is stored at 0xC000
    assert cpu.memory.read(0xC000) == 0x34, "test_ld_a16_sp failed: lower byte incorrect"
    # Check that the upper byte (0x12) is stored at 0xC001
    assert cpu.memory.read(0xC001) == 0x12, "test_ld_a16_sp failed: upper byte incorrect"
    # Check that PC was incremented by 3 (1 for opcode + 2 for address)
    assert cpu.pc == 0x0103, "test_ld_a16_sp failed: PC not incremented correctly"

def main():
    import inspect
    import sys

    # Get the current module
    current_module = sys.modules[__name__]

    # Find all functions that start with 'test_'
    test_functions = []
    for name, obj in inspect.getmembers(current_module):
        if inspect.isfunction(obj) and name.startswith('test_'):
            test_functions.append((name, obj))

    # Sort test functions by name for consistent execution order
    test_functions.sort(key=lambda x: x[0])

    print(f"Running {len(test_functions)} tests...")

    passed = 0
    failed = 0

    for test_name, test_func in test_functions:
        try:
            print(f"Running {test_name}...", end=" ")
            test_func()
            print("PASSED")
            passed += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
