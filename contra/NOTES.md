# Contra (USA) NES — Studio locale di reversing

Scope: analisi locale di `Contra (USA).nes` (prima pagina: dump No-Intro
`c9ea66bb7cb30ad5343f1721b1d4d3219859319b`), disassemblazione, round-trip
byte-identico, annotazione e una patch di prova verificata in emulatore.
Nessun commit, nessuna pubblicazione: solo questo albero.

## Archivio

```
contra/
├── rom/Contra (USA).nes      ROM originale intoccata
├── build/                    primitivi: bank*.bin, .o, contra-rebuilt.nes
├── src/                      listing riassemblabili (ca65)
│   ├── header.s              header iNES ricreato (mapper 2, 8×16KB PRG)
│   ├── symbols.inc           registri PPU/APU (da65 ASMINC)
│   └── bank0.s … bank7.s     8 banchi PRG da $8000 (b7 = $C000), con commenti
├── info/                     sorgenti di verità per da65
│   ├── bankN.info            generati da gen-info.sh
│   ├── bankN.ranges          zone code/data dal classificatore
│   ├── seeds.txt             seed manuali di codice (modificabile)
│   └── bankN.labels          (opzionale) label manuali
├── tools/
│   ├── cc65/                 cc65/da65/ld65 costruiti da sorgente
│   ├── classify.py           classificatore code/data
│   └── jsnes-test/           harness emulatore headless (jsnes via npm)
├── link.cfg                  ld65: header + 8 banchi PRG
├── Makefile                  ranges → info → listing → link → verify
├── RAM.md                    mappa RAM $0000-$07FF
└── NOTES.md                  questo file
```

## Step 1 — Header iNES

- Mapper 2 (UxROM): PRG commutabile a $8000, banco fisso a $C000.
- 8 × 16 KB PRG (128 KB), 0 CHR ⇒ CHR-RAM (il gioco carica tile via PPU).
- Mirroring verticale (byte 6 = $21).
- I PRG banchi 0-6 vivono a $8000 (commutabili), il banco 7 a $C000 (fisso,
  contiene RESET=$C001, NMI=$C060, IRQ=$C0B5 → solo `rti`).

## Step 2 — Disassemblaggio con da65

- Info file per banco (`info/bankN.info` → da65 `-i … -o src/bankN.s`).
- Sintassi info file: commenti `#` (non `;`), niente `OUTPUTNAME` (il nome
  d'uscita va su CLI), `ASMINC { FILE "src/symbols.inc" }` così da65 emette i
  nomi registro direttamente nel listing (ca65 non serve un include).
- `--comments 4` per riga con indirizzo+byte+ASCII: ogni riga del listing
  porta il suo dump, utile per revisione umana e per i byte-safe.
- Il `.code` emesso da da65 è rimosso via sed nel Makefile.
- **Bug risolto**: `da65/src/da65/comments.c` — `NewComment()` chiamava
  `strlen(NULL)` sui simboli ASMINC senza commento → segfault. Patch locale
  mantenuta in `tools/cc65/`.
- **CPU = "6502"** (solo ufficiali). `6502X` scartato: ca65 normalizza le
  codifiche multiple degli opcode non ufficiali a una sola → 289 byte di
  differenza al link. Il classificatore si ferma su byte non ufficiali, che
  finiscono in `.byte`: è byte-safe per costruzione.

## Step 3 — Code/data classification e round-trip

- `tools/classify.py`: discesa ricorsiva da vettori + entry note, seeding
  cross-bank iterativo (10 giri), rilevamento tabelle di indirizzi, stop su
  byte sconosciuti. Output `info/bankN.ranges` (da65 `RANGE`).
- Seed manuali in `info/seeds.txt`: indirizzi (esadecimale, commenti `;`)
  scoperti leggendo tabelle jump inline che da65 mostrava come `.byte`
  (`jsr LC857` con word immediati = dispatcher a indirizzi noti solo a runtime).
- `make verify`: ricostruisce la ROM e stampa `IDENTICAL OK` con SHA-1 uguale
  all'originale. Target `&:` (make ≥ 4.4) perché `gen-info.sh` giri una volta
  sola anche con `-j` (corruttori di info file in corsa).
- Code% per banco (stato attuale): b0 9.3%, b1 13.7%, b2 6.7%, b3 1.8%,
  b4 2.7%, b5 2.1%, b6 5.8%, b7 59.3%. I banchi "dati" contengono CHR tile e
  mappe livello; il codice nascosto è quasi tutto recuperato in bank7.

## Step 4 — Architettura del gioco (annotazioni principali)

Dettagli in `src/bank7.s`/`src/bank1.s` inline e in `RAM.md`.

- **Main loop** (bank7 $C057): gira un RNG (`lda $1A/adc $34/sta $34`) e basta;
  tutta la logica vive nell'NMI.
- **NMI $C060**: fast-path (bit0 di `$1A`) che salta l'upload VBlank, shadow
  `$FF`/`$FE` (PPUCTRL/PPUMASK) su $2000/$2001.
- **Dispatcher stati** `$18` via `jsr LC857` con tabella word immediata dopo la
  JSR (pattern "inline jump table"): $C25B titolo, …, $CE30 in-game.
  Sotto-stati `$2C` con tabella a $CE35 (11 voci): $CE4B init livello (copia
  32 byte di `$40-$5F` da $B319+stage*32), $D02E frame gameplay.
- **Frame gameplay** (LCEF7) = 5 chiamate bancali (bank3 scroll, bank0 enemy
  loop, bank2 ×3). Thunks: `LC139` salva banco in `$07EC` e seleziona,
  `LC146` ripristina; le entrate cross-bank restano letterali `$xxxx`.
- **Bank switching**: write registro UxROM via `sta LFFD0,y` (tabella id a
  $FFD0). Byte-firma bank-id a $8000 per debug.
- **Joypad** `LC397`/`LC35B`: `$04/$05` raw, `$F1/$F2` held, `$F5/$F6` edge
  (newly pressed), `$F9/$FA` prev.
- **Player controller** (bank7 $D4xx-$E6xx, quasi tutto recuperato):
  variabili zp per giocatore (X=0/1) — `$90` vite, `$94/$96` posizione,
  `$98` subpixel X, `$9A` vx, `$A0` grounded, `$A4` pose, `$C4` subpixel Y,
  **`$C6` vy** (negativo = su, gravità +1/frame, landing azzera),
  `$BC` azione. Salto: `LD6D3` sceglie vy iniziale **$FB o $FC** in base al
  bit0 di `$40` (parametro stage) e subpixel `$F0`/`$90`.
- **Oggetti bank1**: 6 slot stride-6 a `$0100+X` (timer, tipo, flags, PC script
  `$0112/$0118`); `$012F` globale che ferma tutto tranne il giocatore (tipo
  $54). Spawn via stream `LC8E3`→`LC9A3`. Il banco1 ospita anche la
  sequencer SFX per oggetto (scrive `SQ1_VOL,x`).
- **Sprite**: 26 slot SoA stride $1A a `$0300+X` (id, Y=$031A, X=$0334,
  meta=$034E), OAM shadow $0200, builder `LAE9D` con tabelle $LB02E/$LB12E.
- **Scrolling** (bank7 $DC4B): `$64/$65` contatore 16-bit, `$60` colonna,
  flip nametable via `eor #$01` su `$FF`, fine stage quando `$64 == $48`.
- **Enemy loop** bank0 $E61E: 16 slot `$04B8+X`, tipo `$0528+X` → jump table
  $E6A8 con dispatch indiretto (`jmp ($04)`).

## Step 6 — Patch di prova: velocità di salto

1. Costante trovata staticamente: `LDA #$FB` a $D6E8 (e varianti $FC a $D6EE)
   nel player controller di bank7.
2. `make verify` verde (round-trip) → poi patch: in `src/bank7.s`
   `lda #$FB` → `lda #$F8`, `make build/contra-rebuilt.nes`. `cmp -l` contro
   l'originale: **1 byte solo** (offset 120570).
3. Verifica dinamica con `tools/jsnes-test/` (jsnes npm, headless):
   - `run.mjs <rom> <script.json>`: alimenta joypad (byte NES standard:
     A=$80, START=$10, RIGHT=$01…), fa N frame, dumpa RAM $0000-$07FF e OAM,
     salva screenshot PPM (convertibili con ImageMagick).
   - Script: START a f300 → gameplay ~f850 → premi A a f900.
   - Trace RAM `$C6` (vy): originale `fb fc fc fd fe ff 00…`, patchato
     `f8 f9 fa fb fc fd…` — gravità +1/frame identica, vy iniziale più
     negativa: salto più alto e più lungo, esattamente come previsto.
   - Screenshot f915: giocatore a terra (originale) vs giocatore in alto
     nello sky (patchato). Il gioco continua a funzionare (1000 frame, niente
     crash).
4. Patch annullata (`lda #$FB` ripristinato), `make verify` di nuovo
   `IDENTICAL OK`: l'albero torna allo stato round-trip verde.

## Step 7 — Scelte e note varie

- cc65 costruito da sorgente (`tools/cc65/bin`) perché `sudo` richiede
  password non disponibile.
- Listing "byte-safe": tutto ciò che il classificatore non sa raggiungere
  resta `.byte` con indirizzo+dump; le label cross-bank restano letterali.
  Questo garantisce il round-trip anche dove l'analisi è incompleta.
- `info/seeds.txt` è l'unico posto da toccare per far emergere nuovo codice:
  aggiungi l'indirizzo, `make`, e i listing si arricchiscono senza mai
  rompere la verifica.
- Nessun emulatore di sistema disponibile: l'harness jsnes copre il bisogno
  (input, RAM/OAM dump, screenshot) e si appoggia solo a npm.
- `LXX` (label auto di da65) sono locali al file di banco; i riferimenti
  cross-bank `$xxxx` sono volutamente letterali.
- Ispirazione/nota legale: analisi interoperativa di prima pagina per studio
  personale (EU Dir. 2009/24/EC art. 5, 17 U.S.C. §1201(f)). Nessuna
  redistribuzione della ROM.
