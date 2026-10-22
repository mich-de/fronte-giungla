#!/usr/bin/env python3
"""Write cheat variants of Contra (USA): build/contra-god.nes, build/contra-30vite.nes.

Byte patches to PRG bank 7 (fixed at $C000); same table as CHEATS in nes/index.html.
Each patch checks the original byte first, so a different dump is refused.
"""
import sys

ROM = sys.argv[1] if len(sys.argv) > 1 else "rom/Contra (USA).nes"

GOD = [(0xE2C1, 0xB5, 0xA9),   # lda $AE,x -> lda #$AE: enemy/bullet collision skip always taken
       (0xDA03, 0xD6, 0xB5)]   # dec $32,x -> lda $32,x: falling into a pit never costs a life
LIVES30 = [(0xC462, 0x02, 0x1D)]  # starting lives 2 -> 29 (REST 30), the Konami code value

VARIANTS = {"build/contra-god.nes": GOD, "build/contra-30vite.nes": LIVES30}


def prg7(addr):
    return 0x10 + 7 * 0x4000 + (addr - 0xC000)


rom = open(ROM, "rb").read()
for out, patches in VARIANTS.items():
    data = bytearray(rom)
    for addr, orig, new in patches:
        if data[prg7(addr)] != orig:
            sys.exit(f"{ROM}: ${addr:04X} is ${data[prg7(addr)]:02X}, expected ${orig:02X} (not Contra (USA)?)")
        data[prg7(addr)] = new
    open(out, "wb").write(data)
    print(out)
