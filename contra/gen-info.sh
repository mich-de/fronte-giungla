#!/usr/bin/env bash
# Generate da65 info files:
#   header (GLOBAL/ASMINC/SEGMENT) + hand labels (info/bankN.labels)
#   + auto code/data ranges (info/bankN.ranges from tools/classify.py)
set -e
cd "$(dirname "$0")"
mkdir -p info
[ -f info/bank0.ranges ] || { echo "run tools/classify.py first"; exit 1; }
for i in 0 1 2 3 4 5 6; do
  cat > info/bank$i.info <<EOF
GLOBAL {
    INPUTNAME   "build/bank$i.bin";
    STARTADDR   \$8000;
    PAGELENGTH  0;
    CPU         "6502";
};
ASMINC { FILE "src/symbols.inc"; };
SEGMENT { START \$8000; END \$BFFF; NAME "BANK$i"; };
EOF
  cat info/bank$i.ranges >> info/bank$i.info
done
cat > info/bank7.info <<'EOF'
GLOBAL {
    INPUTNAME   "build/bank7.bin";
    STARTADDR   $C000;
    PAGELENGTH  0;
    CPU         "6502";
};
ASMINC { FILE "src/symbols.inc"; };
SEGMENT { START $C000; END $FFFF; NAME "BANK7"; };

# Hardware vectors (file offset $3FFA of bank7)
RANGE { START $FFFA; END $FFFF; TYPE WordTable; };
LABEL { NAME "vec_nmi";   ADDR $FFFA; };
LABEL { NAME "vec_reset"; ADDR $FFFC; };
LABEL { NAME "vec_irq";   ADDR $FFFE; };
EOF
# hand-written labels (non-vector) for banks 0-6 if present
for i in 0 1 2 3 4 5 6; do
  [ -f info/bank$i.labels ] && cat info/bank$i.labels >> info/bank$i.info
done
[ -f info/bank7.labels ] && cat info/bank7.labels >> info/bank7.info
cat info/bank7.ranges >> info/bank7.info
echo "info files generated"
