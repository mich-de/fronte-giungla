# Contra (USA) NES - reassemblable disassembly build
# Verify: make verify  -> SHA-1 of rebuilt ROM must match original
CC65BIN := tools/cc65/bin
DA65    := $(CC65BIN)/da65
CA65    := $(CC65BIN)/ca65
LD65    := $(CC65BIN)/ld65
ORIG    := rom/Contra (USA).nes
OUT     := build/contra-rebuilt.nes
BANKS   := 0 1 2 3 4 5 6 7
SRCS    := $(addprefix src/bank,$(addsuffix .s,$(BANKS))) src/header.s
OBJS    := $(addprefix build/obj-bank,$(addsuffix .o,$(BANKS))) build/obj-header.o
RAMDISK :=

# bank start addresses: 0-6 switchable @ $8000, bank7 fixed @ $C000
START_7 := $$C000

all: verify

# disassemble: da65 + inject .include of symbols.inc after .setcpu line
src/bank%.s: build/bank%.bin info/bank%.info src/symbols.inc
	$(DA65) --comments 4 -i info/bank$*.info -o src/bank$*.s.tmp
	sed -e 's/^[[:space:]]*\.code[[:space:]]*$$/; (da65 default segment switch removed)/' \
	    src/bank$*.s.tmp > src/bank$*.s
	rm -f src/bank$*.s.tmp

build/obj-bank%.o: src/bank%.s src/symbols.inc
	$(CA65) --include-dir src -o $@ src/bank$*.s

build/obj-header.o: src/header.s
	$(CA65) -o $@ src/header.s

$(OUT): $(OBJS) link.cfg
	$(LD65) -C link.cfg -o $@ $(OBJS)

# code/data classification -> info/bankN.ranges
ranges: $(addprefix build/bank,$(addsuffix .bin,$(BANKS)))
	python3 tools/classify.py

# all info files from ONE recipe (grouped targets: no concurrent gen-info)
INFOS := $(addprefix info/bank,$(addsuffix .info,$(BANKS)))
RANGES := $(addprefix info/bank,$(addsuffix .ranges,$(BANKS)))
$(INFOS) &: gen-info.sh $(RANGES) src/symbols.inc
	bash gen-info.sh

verify: $(OUT)
	@echo "--- SHA1 original vs rebuilt"
	@sha1sum "$(ORIG)" $(OUT)
	@a=$$(sha1sum "$(ORIG)" | cut -d' ' -f1); b=$$(sha1sum $(OUT) | cut -d' ' -f1); \
	if [ "$$a" = "$$b" ]; then echo "IDENTICAL OK"; else echo "MISMATCH"; exit 1; fi

cheats: $(OUT)
	python3 tools/cheats.py "$(ORIG)"

info: gen-info.sh
	bash gen-info.sh

.SECONDARY:

clean:
	rm -f src/bank*.s src/bank*.s.tmp build/obj-*.o $(OUT)

.PHONY: all verify info clean cheats
