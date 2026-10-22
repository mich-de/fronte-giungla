#!/usr/bin/env bash
# Extract the 8 PRG banks from a locally supplied iNES ROM into build/bankN.bin.
# Input: rom/Contra (USA).nes (user-supplied, never committed: *.nes is gitignored).
# Layout: 16-byte iNES header + 8 x 16KB PRG, 0 CHR (mapper 2 / UxROM).
# Bank order = file order: banks 0-6 switchable @ $8000, bank 7 fixed @ $C000.
set -e
cd "$(dirname "$0")/.."
ROM="rom/Contra (USA).nes"
[ -f "$ROM" ] || { echo "missing $ROM — place your own legally obtained dump there"; exit 1; }
mkdir -p build
# strip 16-byte header (tail -c +17 = start at byte 17), then split 16KB chunks
tail -c +17 "$ROM" > build/prg.tmp
sz=$(stat -c%s build/prg.tmp)
[ "$sz" -eq 131072 ] || { echo "unexpected PRG size $sz (want 131072)"; exit 1; }
for i in 0 1 2 3 4 5 6 7; do
  dd if=build/prg.tmp of="build/bank$i.bin" bs=16384 skip=$i count=1 status=none
done
rm -f build/prg.tmp
echo "extracted 8 PRG banks -> build/bankN.bin"
