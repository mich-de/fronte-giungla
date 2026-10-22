#!/usr/bin/env python3
"""Classify Contra PRG banks into code/data ranges via recursive traversal.

- Seeds: CPU vectors (bank7) + absolute JSR/JMP targets (cross-bank refs
  seed every bank containing the target) + jump/addr tables discovered in
  data (targets seeded in the bank that holds the table).
- Iterates to fixpoint across banks.
- Emits info/<bank>.ranges with RANGE { ... TYPE Code/ByteTable/AddrTable }.
- Byte safety: any classification round-trips (da65 emits raw bytes either
  way); broken paths (unknown opcode, out-of-segment branch) are NOT marked
  code so da65 never emits an unassemblable branch.
"""
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANKS = 8
BANK_SIZE = 0x4000
BASE = [0x8000] * 7 + [0xC000]  # CPU address of bank start

# ---------------------------------------------------------------- opcode table
# mode -> length
MODE_LEN = {'imp':1, 'imm':2, 'zp':2, 'zpx':2, 'zpy':2, 'izx':2, 'izy':2,
            'abs':3, 'absx':3, 'absy':3, 'ind':3, 'rel':2}

T = {}  # code -> (len, kind, oper)  kind: seq|jmp|jsr|br|stop

def add(codes, mode, kind='seq'):
    for c in codes:
        T[c] = (MODE_LEN[mode], kind, mode)

# official opcodes: mnemonic -> {mode: opcode}
OFFICIAL = {
 'ADC': {'imm':0x69,'zp':0x65,'zpx':0x75,'abs':0x6D,'absx':0x7D,'absy':0x79,'izx':0x61,'izy':0x71},
 'AND': {'imm':0x29,'zp':0x25,'zpx':0x35,'abs':0x2D,'absx':0x3D,'absy':0x39,'izx':0x21,'izy':0x31},
 'ASL': {'imp':0x0A,'zp':0x06,'zpx':0x16,'abs':0x0E,'absx':0x1E},
 'BIT': {'zp':0x24,'abs':0x2C},
 'CMP': {'imm':0xC9,'zp':0xC5,'zpx':0xD5,'abs':0xCD,'absx':0xDD,'absy':0xD9,'izx':0xC1,'izy':0xD1},
 'CPX': {'imm':0xE0,'zp':0xE4,'abs':0xEC},
 'CPY': {'imm':0xC0,'zp':0xC4,'abs':0xCC},
 'DEC': {'zp':0xC6,'zpx':0xD6,'abs':0xCE,'absx':0xDE},
 'EOR': {'imm':0x49,'zp':0x45,'zpx':0x55,'abs':0x4D,'absx':0x5D,'absy':0x59,'izx':0x41,'izy':0x51},
 'INC': {'zp':0xE6,'zpx':0xF6,'abs':0xEE,'absx':0xFE},
 'JMP': {'abs':0x4C,'ind':0x6C},
 'JSR': {'abs':0x20},
 'LDA': {'imm':0xA9,'zp':0xA5,'zpx':0xB5,'abs':0xAD,'absx':0xBD,'absy':0xB9,'izx':0xA1,'izy':0xB1},
 'LDX': {'imm':0xA2,'zp':0xA6,'zpy':0xB6,'abs':0xAE,'absy':0xBE},
 'LDY': {'imm':0xA0,'zp':0xA4,'zpx':0xB4,'abs':0xAC,'absx':0xBC},
 'LSR': {'imp':0x4A,'zp':0x46,'zpx':0x56,'abs':0x4E,'absx':0x5E},
 'ORA': {'imm':0x09,'zp':0x05,'zpx':0x15,'abs':0x0D,'absx':0x1D,'absy':0x19,'izx':0x01,'izy':0x11},
 'ROL': {'imp':0x2A,'zp':0x26,'zpx':0x36,'abs':0x2E,'absx':0x3E},
 'ROR': {'imp':0x6A,'zp':0x66,'zpx':0x76,'abs':0x6E,'absx':0x7E},
 'SBC': {'imm':0xE9,'zp':0xE5,'zpx':0xF5,'abs':0xED,'absx':0xFD,'absy':0xF9,'izx':0xE1,'izy':0xF1},
 'STA': {'zp':0x85,'zpx':0x95,'abs':0x8D,'absx':0x9D,'absy':0x99,'izx':0x81,'izy':0x91},
 'STX': {'zp':0x86,'zpy':0x96,'abs':0x8E},
 'STY': {'zp':0x84,'zpx':0x94,'abs':0x8C},
}
for mn, modes in OFFICIAL.items():
    for mode, c in modes.items():
        T[c] = (MODE_LEN[mode], 'seq', mode)

# implied / flags / stack / transfers
for c in [0x18,0x38,0x58,0x78,0xB8,0xD8,0xF8,0x0A,0x2A,0x4A,0x6A,0xAA,0x8A,
          0xA8,0x98,0xBA,0x9A,0xCA,0xE8,0x88,0xC8,0xEA,0x08,0x28,0x48,0x68]:
    T[c] = (1, 'imp' if False else 'seq', 'imp')
T[0x40] = (1, 'stop', 'imp')               # RTI
T[0x60] = (1, 'stop', 'imp')               # RTS
T[0x00] = (1, 'stop', 'imp')               # BRK

# branches (rel)
for c in [0x90,0xB0,0xF0,0x30,0xD0,0x10,0x50,0x70]:
    T[c] = (2, 'br', 'rel')
# flow
T[0x20] = (3, 'jsr', 'abs')
T[0x4C] = (3, 'jmp', 'abs')
T[0x6C] = (3, 'jmp', 'ind')                # target unknown -> stop path

# (unofficial opcodes intentionally NOT decoded: da65 runs in 6502 mode,
#  any such byte stops a traversal path -> becomes ByteTable = byte-safe)

def load(bank):
    with open(os.path.join(ROOT,'build',f'bank{bank}.bin'),'rb') as f:
        return f.read()

def classify2(bank, seeds, extra_seeds=None):
    """Returns (code offsets, flags, xrefs) for one bank."""
    data = load(bank)
    base = BASE[bank]
    code = set()
    flags = []
    xrefs = set()
    all_seeds = set(seeds)
    if extra_seeds:
        all_seeds |= extra_seeds
    work = [s-base for s in all_seeds if 0 <= s-base < BANK_SIZE]
    seen = set()
    while work:
        off = work.pop()
        while True:
            if off in seen or not (0 <= off < BANK_SIZE):
                break
            seen.add(off)
            b = data[off]
            if b not in T:
                flags.append((base+off, f'unknown opcode ${b:02X}'))
                break
            length, kind, oper = T[b]
            if off + length > BANK_SIZE:
                flags.append((base+off, 'instr crosses bank end'))
                break
            addr = base + off
            if oper == 'abs':
                target = data[off+1] | (data[off+2] << 8)
                if kind in ('jsr','jmp') and 0x8000 <= target <= 0xFFFF:
                    xrefs.add(target)
                toff = target - base
                inseg = 0 <= toff < BANK_SIZE
                if kind == 'jmp':
                    if not (0x8000 <= target <= 0xFFFF):
                        flags.append((addr, f'jmp to ${target:04X}'))
                        break                    # garbage; not code
                    code.update(range(off, off+length))
                    if inseg:
                        work.append(toff)
                    break                        # no fallthrough
                if kind == 'jsr':
                    code.update(range(off, off+length))
                    if inseg:
                        work.append(toff)
                    off += length                 # fallthrough
                    continue
                # plain abs: mark and continue
                code.update(range(off, off+length))
                off += length
                continue
            if oper == 'rel':
                disp = data[off+1]
                if disp >= 0x80: disp -= 0x100
                t = addr + 2 + disp
                toff = t - base
                if not (0 <= toff < BANK_SIZE):
                    flags.append((addr, f'branch out of segment -> ${t:04X}'))
                    break                        # garbage path; not code
                code.update(range(off, off+length))
                work.append(toff)
                off += length
                continue
            # imp / imm / zp / iz / ind
            code.update(range(off, off+length))
            if kind == 'stop':
                break
            off += length
    return code, flags, xrefs

def detect_addr_tables(bank, code):
    """Runs of >=4 words inside data pointing into this bank's code."""
    data = load(bank)
    base = BASE[bank]
    runs = []
    i = 0
    while i + 8 <= BANK_SIZE:
        if i in code:
            i += 1
            continue
        j = i
        good = 0
        total = 0
        while j + 2 <= BANK_SIZE and j not in code:
            w = data[j] | (data[j+1] << 8)
            total += 1
            if (w - base) in code:
                good += 1
            j += 2
        if total >= 4 and good >= max(3, total - 1):
            runs.append((i, j))
        i = max(j, i+1)
    return runs

def main():
    bank_seeds = {i: set() for i in range(BANKS)}
    bank_seeds[7] = {0xC001, 0xC060, 0xC0B5}     # RESET / NMI / IRQ (little-endian vectors)
    sf = os.path.join(ROOT,'info','seeds.txt')
    if os.path.exists(sf):
        for line in open(sf):
            line = line.split(';')[0].strip()
            if not line:
                continue
            a = int(line.replace('$',''),16)
            for i in range(BANKS):
                if BASE[i] <= a < BASE[i]+BANK_SIZE:
                    bank_seeds[i].add(a)

    all_xrefs = set()
    results = {}
    for it in range(10):
        changed = False
        for b in range(BANKS):
            code, flags, xs = classify2(b, bank_seeds[b])
            # addr-table targets (same bank) seed next round
            tables = detect_addr_tables(b, code)
            data = load(b)
            for s,e in tables:
                for j in range(s, e, 2):
                    tgt = data[j] | (data[j+1] << 8)
                    if BASE[b] <= tgt < BASE[b]+BANK_SIZE and tgt not in bank_seeds[b]:
                        bank_seeds[b].add(tgt); changed = True
            new = xs - all_xrefs
            if new:
                all_xrefs |= new
                changed = True
                for t in new:
                    for i in range(BANKS):
                        if BASE[i] <= t < BASE[i]+BANK_SIZE:
                            bank_seeds[i].add(t)
            results[b] = (code, flags, tables)
        if not changed:
            break
    write_ranges(results)

def write_ranges(results):
    os.makedirs(os.path.join(ROOT,'info'), exist_ok=True)
    stats = []
    for b in range(BANKS):
        code, flags, tables = results[b]
        table_bytes = set()
        for s,e in tables:
            table_bytes.update(range(s,e))
        ivals = []
        csorted = sorted(code - table_bytes)
        i = 0
        while i < len(csorted):
            j = i
            while j+1 < len(csorted) and csorted[j+1] == csorted[j]+1:
                j += 1
            ivals.append((csorted[i], csorted[j]+1, 'Code'))
            i = j+1
        for s,e in tables:
            ivals.append((s,e,'AddrTable'))
        data_ivals = []
        covered = sorted([(s,e) for s,e,_ in ivals])
        pos = 0
        for s,e in covered:
            if pos < s:
                data_ivals.append((pos,s))
            pos = max(pos, e)
        if pos < BANK_SIZE:
            data_ivals.append((pos, BANK_SIZE))
        for s,e in data_ivals:
            ivals.append((s,e,'ByteTable'))
        ivals.sort()
        base = BASE[b]
        with open(os.path.join(ROOT,'info',f'bank{b}.ranges'),'w') as f:
            f.write(f'# auto-generated by tools/classify.py - bank{b} '
                    f'(${base:04X}-${base+BANK_SIZE-1:04X})\n')
            for s,e,t in ivals:
                sa, ea = base+s, base+e-1
                # bank7: hardware vectors $FFFA-$FFFF handled in info/bank7.labels
                if b == 7:
                    if sa >= 0xFFFA:
                        continue
                    if ea >= 0xFFFA:
                        ea = 0xFFF9
                f.write(f'RANGE {{ START ${sa:04X}; END ${ea:04X}; TYPE {t}; }};\n')
        ncode = len(code)
        stats.append((b, ncode, len(flags), len(tables)))
    for b,nc,nf,nt in stats:
        print(f'bank{b}: code {nc}/{BANK_SIZE} ({100*nc/BANK_SIZE:.1f}%), '
              f'addr-tables {nt}, flags {nf}')
    nflag = 0
    for b in range(BANKS):
        for addr,msg in results[b][1]:
            nflag += 1
            if nflag <= 40:
                print(f'  FLAG bank{b} ${addr:04X}: {msg}', file=sys.stderr)
    print(f'total flags: {nflag}', file=sys.stderr)

if __name__ == '__main__':
    main()
