; iNES header, byte-identical to original Contra (USA).nes
; 8x16KB PRG (mapper 2 / UxROM), 0 CHR -> CHR-RAM, vertical mirroring ($21)
.segment "HEADER"
        .byte   "NES", $1A
        .byte   $08             ; PRG ROM size in 16KB units
        .byte   $00             ; CHR ROM size in 8KB units (0 = CHR-RAM)
        .byte   $21             ; mapper 2, vertical mirroring, no battery/trainer/4screen
        .byte   $00             ; mapper high nibble + iNES2 flags
        .byte   $00, $00, $00, $00, $00, $00, $00, $00  ; padding
