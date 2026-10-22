; symbols.inc - RAM/hardware register names shared by da65 (ASMINC) and ca65
; ONLY absolute RAM/IO addresses live here (never ROM labels: those are
; per-bank LABEL directives in info/*.info).
; --- PPU registers ($2000-$2007) ---
PPUCTRL   := $2000
PPUMASK   := $2001
PPUSTATUS := $2002
OAMADDR   := $2003
OAMDATA   := $2004
PPUSCROLL := $2005
PPUADDR   := $2006
PPUDATA   := $2007
; --- APU/IO ($4000-$4017) ---
SQ1_VOL   := $4000
SQ1_SWEEP := $4001
SQ1_LEN   := $4002
SQ1_REL   := $4003
SQ2_VOL   := $4004
SQ2_SWEEP := $4005
SQ2_LEN   := $4006
SQ2_REL   := $4007
TRI_LINEAR:= $4008
TRI_LEN   := $400A
TRI_REL   := $400B
NOISE_VOL := $400C
NOISE_LEN := $400E
NOISE_REL := $400F
DMC_FREQ  := $4010
DMC_RAW   := $4011
DMC_START := $4012
DMC_LEN   := $4013
SND_CHN   := $4015
JOY1      := $4016
JOY2      := $4017
