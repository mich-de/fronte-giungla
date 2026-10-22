# RAM Map — Contra (U) — $0000-$07FF

Sources: `src/symbols.inc` (PPU/APU registers emitted by da65 ASMINC),
cross-references in `src/bank*.s`, and headless jsnes RAM/OAM traces
(`tools/jsnes-test/`). Addresses marked (obs) were confirmed by emulator
traces; the rest are inferred from code context and may be incomplete.

## Zero page $0000-$00FF — engine scratch

| Addr | Size | Name (proposed) | Usage |
|------|------|-----------------|-------|
| $00-$03 | 4 | tmp0-3 | General NMI/main temps (LC35B copies $04/$05 here) |
| $04/$05 | 2 | joy_raw_1/2 | Raw joypad byte, both players (LC35B) |
| $06/$07 | 2 | tmp | JOY read temporaries (LC3A2) |
| $0C/$0D | 2 | vram_lo/hi | PPU upload cursor (LC536 area, $0700 buffer) |
| $0E/$0F | 2 | ptr_lo/hi | Upload source pointer (LC536) |
| $10/$11 | 2 | cam_x | Camera/scroll X (CF2E copies $AA/$AB here); $11 also upload temp |
| $14 | 1 | tmp | Upload counter (LC536) |
| $16/$17 | 2 | ptr_lo/hi | Second upload pointer (LC536) |
| $18 | 1 | state | Main state machine (dispatcher `jsr LC857`, table at $C25B: $C25B/$C274/$C2B1/$C2C7/$C2F4/$CE30). 1=title, 3=game start transition, 5=in-game |
| $19 | 1 | state_flag | Set when $18 becomes 3 (obs) |
| $1A | 1 | frame | Frame counter; also RNG seed input; NMI fast-path toggles on bit0 |
| $1B | 1 | nmi_path | NMI path flag (bit7 gating) |
| $1C | 1 | attract | Nonzero = demo/attract playback |
| $1E | 1 | tmp | LCA61/LCAAD param |
| $20 | 1 | blank_ctr | Vblank counter |
| $21 | 1 | vram_idx | $0700 upload buffer index (LC536/CE4B) |
| $22 | 1 | menu_ctr | Title menu counter (LC3DB) |
| $23 | 1 | music_req | Music/sound request ($FF = stop, $01/$C0 etc.) |
| $25 | 1 | pause | Nonzero = paused (LCEE3) |
| $28 | 1 | title_tm | Title/attract timer ($A4 init, LC3F3/LC40F) |
| $29 | 1 | sfx_req | Sound request ($60, LCF0A) |
| $2A | 1 | sfx_alt | Alternate sound request (LCE7E) |
| $2B | 1 | retry | Set to 2 on game restart (LC32C) |
| $2C | 1 | substate | In-game sub-dispatcher index, table at $CE35 (11 entries: $CE4B level init … $D02E) |
| $2D | 1 | subtimer | Substate timer (LCF27) |
| $24 | 1 | konami | Konami code entered on title: lives init uses $1D instead of $02 (C461) |
| $30 | 1 | stage | Stage id 0-7: indexes $40 param copy ($B319+stage*32), scroll table $CEC8 |
| $32/$33 | 2 | lives | Lives left, player 0/1 (obs): 2 at start = REST 3, 0 = last life; init C461, `dec` on death DA03, extra life C502 (max $63) |
| $34/$35 | 2 | rng | LFSR-ish RNG ($1A+$34 adc chain in main spin loop) |
| $37 | 1 | flag | Checked before death/continue (D713/D833) |
| $38/$39 | 2 | death_req | Both nonzero → death sequence (LCEEE) |
| $3B | 1 | dead | Player death flag (LCEEA→LCF25, LCE65) |
| $40-$5F | 32 | stage_params | Copied from bank data $B319 + stage*32 at level init (CE4B). $40 bit0 selects jump velocity #$FB vs #$FC (D6E5). Many stage constants ($48 = scroll length, …) |
| $60 | 1 | scroll_col | Column counter 0-$1F (DC78/DCA4) |
| $62 | 1 | scroll_blk | Blocks per nametable flip (DCAE) |
| $64/$65 | 2 | scroll_pos | 16-bit horizontal scroll counter (inc pair at DC78) |
| $68/$69 | 2 | scroll_v / mirror | Scroll velocity addend; $69 bit6 = mirroring flip (DCAA) |
| $6A | 1 | stop_scroll | $FF stops scrolling (LCED8/CF2E) |
| $71 | 1 | eof | Stage-scroll end flag (DCC9) |
| $75/$76 | 2 | pause_tm | Pause/countdown timers (LDC59) |
| $77 | 1 | scroll_bias | Added to $68 (LDC6F) |
| $82 | 1 | tmp | Cleared per nametable flip (LDC8B) |
| $84 | 1 | death_ct | Incremented on timer expiry (LDC69) |
| $90/$91 | 2 | p_state | Player state, player 0/1 (1 checked at D40E/D46C; set from LDAD1 on death D9FD). Not lives: see $32 |
| $94/$95 | 2 | px_lo | Player X position low + $9A high byte math (D843) |
| $96/$97 | 2 | py | Player Y position low (D5F3 clears with $98) |
| $98/$99 | 2 | px_sub | Player X subpixel accumulator; += $D4 (D5FB) |
| $9A/$9B | 2 | vx | Player horizontal velocity (D845: $94 += $9A) |
| $9E/$9F | 2 | vx_lock | Horizontal velocity lock/knockback (D871) |
| $A0/$A1 | 2 | grounded | Ground/ceiling state; nonzero = grounded (D6DD, E21C: vy applied only when !grounded) |
| $A4/$A5 | 2 | pose | Stance/pose flags ($11/$41/$81/$91 written at D6DB/D6C7) |
| $A6,$A8,$AC,$B0 | | misc_state | Cleared at init/respawn (DAF7-DAFF) |
| $AE/$AF | 2 | invuln | Invincibility timer, player 0/1 (obs): $7F after respawn, `dec` per frame D467; nonzero skips enemy collision E2C1 and blinks the sprite (bank2 B004) |
| $AA/$AB | 2 | cam_save | Saved camera X (CF2E) |
| $B2/$B4 | 2 | air_flag / dir | $B2 nonzero = airborne-specific input; $B4 = facing (1 at init) |
| $B8 | 2 | tmp | Direction temp (D6CB) |
| $BA/$BB | 2 | weapon? | Checked before jump (D5C7 cmp #1), sets $A4=$40 (D5DB) |
| $BC/$BD | 2 | action | Action id: 1 jump, 2 fire?, 3/5/8 set at D66B/D6AB/D73B/D83B |
| $C0,$C2 | 2 | state2 | $C2 cmp #5 selects $A0=$91 vs $11 at jump (D6D3) |
| $C4/$C5 | 2 | py_sub | Player Y subpixel; jump init $F0 or $90 (D6F5); observed +0x23/frame during arc (obs) |
| $C6/$C7 | 2 | vy | **Player Y velocity**; jump init **$FB / $FC** (D6E8/D6EE); gravity +1/frame; landing zeroes it (D7EB). Negative = up |
| $C8/$C9 | 2 | tmp | Checked at D67F (death path) |
| $CA,$D0,$D2 | | death_sub | Death sequence substates (D66D-D677, D73F) |
| $D4/$D5 | 2 | dx | X-subpixel increment added to $98 (D5FB) |
| $D6/$D7 | 2 | ground_id | Ground/solid id, cmp #$17 (D63E/D6DB) |
| $D8/$D9 | 2 | flags | Bit6/low6 flag pair (D87C-D886) |
| $E4/$E5 | 2 | ptr | Scratch pointer (L8154 music/SFX seq) |
| $F1/$F2 | 2 | held | Joypad held, player 1/2 (LC386) |
| $F3 | 1 | tmp | JSR-safe temp (LC193) |
| $F5/$F6 | 2 | press | Joypad newly-pressed (edge), players 1/2 (LC38D) |
| $F7 | 1 | ysave | Y-register spill for bank thunks (LC183/LC193) |
| $F9/$FA | 2 | prev | Previous joypad state (LC391) |
| $FD | 1 | scroll_x | PPU scroll X used by NMI; cleared on title/game start (LC3F9) |
| $FE | 1 | ppumask | PPUMASK shadow ($1E = rendering on, C0E7) |
| $FF | 1 | ppuctrl | PPUCTRL shadow; toggled bit0 per nametable flip (LDC8F), $B0/$B1 |

## Page $0100-$01FF — bank1 object/script system (6 logical slots)

Stride-6 arrays indexed by X (loop at $80DC, `cpx #$06`):

| Addr | Usage |
|------|-------|
| $0100+X | Timer; when it hits 0 the object retires (L8115→L8259) |
| $0106+X | Object type (0 = free). $38 = common enemy, $54 = player, … |
| $010C+X | Script/opcode temp (L83xx) |
| $0112+X | Script pointer low (obs: $112-$115 change as PC advances, $0114 = mid byte) |
| $0118+X | Script pointer save (PC load/advance at L861D/L862A) |
| $011E+X | SFX id (bmi branch; feeds music table at $8001, L8154) |
| $0120 | Slot index (stashed at loop top, L80DC) |
| $0123 | Y-arg index (L80DF) |
| $0124+X | Flags (bits $04 done, $06, $20, $41) |
| $012A+X | SFX sequence counter (L8163) |
| $012F | Global gate: when nonzero only type $54 (player) updates (L8103) |
| $0130+X | Timer compare (L81AC) |
| $0132+X | Opcode offset (L8395 area) |
| $013C | SFX pitch bias (L817A) |
| $014E+X | SFX volume mask (L8181) |
| $015A,X | Opcode shift (L83xx) |
| $0160+X | SFX duration counter (L8172/L81BD) |
| $0178+X/$017A+X/$017E+X | Per-object SFX pitch state, players only (x<2, L812D-L813B) |

Spawn entry: `LC9A3` (stream at `LC8E3`; `LDA #$90/STA $90` = lives init lives in the spawn path).

## Page $0200-$02FF — OAM shadow (DMA'd to PPU)

## Page $0300-$03FF — sprite system (26 slots, stride $1A)

| Addr | Usage |
|------|-------|
| $0300+X | Sprite id / alive (LAE9D) |
| $030A+X | Enabled flag (LE633) |
| $031A+X | Sprite Y (LE204, LAE9D) |
| $0324+X | Y bound check #$9C (LE640) |
| $0334+X | Sprite X (LE252, LAE9D) |
| $034E+X | Meta/flip byte (LAEE3; tables LB02E/LB12E) |

## Page $0400-$06FF — bank0 enemy/object system (16 slots, X=$0F..0)

| Addr | Usage |
|------|-------|
| $04B8+X | Active flag (LE626) |
| $0528+X | Type → jump table $E6A8 (LE659, dispatched via `jmp ($04)` indirection) |
| $0598+X | Behaviour flags (bit4 = proximity, bit7 = skip LE345; LE617/LE64D) |
| $05C8+X | Per-type state (B94A) |

## Page $0700-$07FF — PPU upload buffer + bank save

| Addr | Usage |
|------|-------|
| $0700-$07FF | VRAM update queue built by LC536-family (control byte, addr, tiles) |
| $07E0/$07E2 | Upload pointers (C528 region) |
| $07EC | Saved bank id (LC139/LC146) |
| $07ED | Saved bank id, bank1 thunk (LC14C/LC15E) |

## Bank-switching contract (UxROM, mapper 2)

- `$8000-$BFFF` = switchable, `$C000-$FFFF` = fixed bank7.
- `LFFD0` = 8-entry bank id table; `STA LFFD0,Y` writes the UxROM register
  (any write to $8000-$FFFF range switches; the store targets the table label).
- Thunks: `LC139` save id→$07EC + select Y, `LC13F` select Y, `LC146` restore,
  `LC14C/LC15E` save/restore with bank1.
- Per-frame gameplay (LCEF7) = `LC1E9`(bank3→$DC4B scroll engine), `LC1C9`
  (bank0→$E61E enemy loop), `LC1D1`(bank2→$B419), `LC1E1`(bank2→$B523),
  `LD105`, `LC1F9`(bank2→$CCB8).
