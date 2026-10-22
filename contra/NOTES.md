# Contra (USA) NES — RE build notes (agent-facing)

Questa nota serve a un agente (Claude o altro) che deve **ricompilare,
rigenerare o ripatchare** questo studio partendo da checkout pulito, senza
problemi di copyright.

## 1. Politica copyright — leggere prima

- **La ROM non è nel repo** e non deve entrarci mai: `.gitignore` esclude
  `*.nes` e `*.zip`. Il file `rom/Contra (USA).nes` va fornito dall'utente,
  da un dump di una sua copia legittima (No-Intro: SHA-1
  `c9ea66bb7cb30ad5343f1721b1d4d3219859319b`). Senza quel file la pipeline
  si ferma a monte: `tools/extract.sh` esce con errore esplicito.
- **Nessun contenuto del gioco è in questo documento** (niente byte, CHR,
  mappe, stringhe). Gli hash sono fatti, non contenuto.
- **`src/bank*.s` è un disassembly derivato** dalla ROM: nel repo serve a
  ricompilare in locale. Se un giorno si vuole distribuire/pubblicare il
  solo progetto "pulito", tenere locali i listing e farli rigenerare dalla
  pipeline (tutto il resto — tool, doc, testi — è originale).
- Base dichiarata per l'analisi di prima pagina: uso privato/
  interoperabilità (EU Dir. 2009/24/EC art. 5, 17 U.S.C. §1201(f)). Non
  ridistribuire la ROM né i binari PRG estratti.
- `build/bank*.bin` e `build/*.o` sono artefatti derivati: rigenerabili, in
  repository servono solo come cache locale (commit OK finché il repo resta
  privato; escludere se si pubblica).

## 2. Prerequisiti

- `make`, `python3`, `bash`, `dd`/`tail` (coreutils).
- Toolchain cc65: **inclusa** in `tools/cc65/bin` (da65/ca65/ld65 già
  buildati). Se manca: `cd tools/cc65 && make -j$(nproc)` (serve gcc).
  Nota: `tools/cc65/src/da65/comments.c` contiene una patch locale obbligatoria
  (`NewComment()` faceva `strlen(NULL)` su simboli ASMINC senza commento →
  segfault). Se si ricompila cc65 da upstream, riapplicare il fix.
- Facoltativo: `npm i` dentro `tools/jsnes-test` per l'harness di verifica
  dinamica (jsnes headless).

## 3. Rebuild veloce (dai listing già nel repo)

```sh
cd contra
make build/contra-rebuilt.nes        # ca65 + ld65, zero ROM necessaria
```

Risultato: `build/contra-rebuilt.nes`. Per la verifica SHA-1 serve la ROM
dell'utente (vedi §4).

## 4. Rigenerazione completa da zero (ROM → listing → ROM)

Ordine delle operazioni (tutto già codificato nel Makefile):

```sh
cd contra
# 1. l'utente mette il proprio dump: rom/Contra (USA).nes
bash tools/extract.sh                # header 16B scartato, 8 x 16KB -> build/bankN.bin
# 2. classificazione code/data -> info/bankN.ranges
python3 tools/classify.py
# 3. info files da65 (ranges + label manuali info/seeds.txt + info/bankN.labels)
bash gen-info.sh
# 4. disassembla e ricompila + verifica round-trip
make -j8 verify
```

Atteso:

```
c9ea66bb7cb30ad5343f1721b1d4d3219859319b  rom/Contra (USA).nes
c9ea66bb7cb30ad5343f1721b1d4d3219859319b  build/contra-rebuilt.nes
IDENTICAL OK
```

`MISMATCH` = un listing non è più byte-identico: controllare se è stato
modificato del codice a mano (una patch intenzionale produce **1 byte** di
differenza, visibile con `cmp -l rom/… build/…`).

Catena Makefile: `info/bankN.info` ← `gen-info.sh` (target raggruppato `&:`,
non rompere: `-j` su target singoli corrompeva gli info) → `src/bankN.s` ←
da65 → `.o` ← ca65 → `build/contra-rebuilt.nes` ← ld65 → `verify`.
`make clean` cancella i listing: sono 100% rigenerabili dai passi 1-4.

Regole tecniche da65/info file (se si riscrive qualcosa):

- commenti info file = `#` (non `;`), niente `OUTPUTNAME` (nome su CLI `-o`)
- `ASMINC { FILE "src/symbols.inc"; }` → i nomi RAM escono già nel listing
- CPU `"6502"` (solo ufficiali). **Non** `6502X`: ca65 collassa le codifiche
  multiple non ufficiali a una canonica → 289 byte di delta. Il
  classificatore si ferma sui byte non ufficiali (finiscono in `.byte`).
- `--comments 4` (indirizzo+byte+ASCII per riga), `.code` rimosso via sed.
- Le label auto `LXX` di da65 sono locali al banco; i riferimenti cross-bank
  restano letterali `$xxxx` — voluto, è ciò che garantisce il round-trip.

## 5. Classificatore e seed

`tools/classify.py`: discesa ricorsiva da vettori (RESET/NMI/IRQ di bank7) +
seed iterativi cross-bank + rilevamento tabelle indirizzi; output
`info/bankN.ranges`. Seed aggiuntivi manuali in `info/seeds.txt` (una riga
per indirizzo esadecimale, commenti `;`).

Per far emergere nuovo codice: aggiungi l'indirizzo a `info/seeds.txt`,
ripeti i passi 2-4, verifica. Come sono stati trovati gli indirizzi esistenti:
letta delle tabelle jump inline (`jsr LC857` con word immediati subito dopo la
JSR, mostrate da65 come `.byte`) e tracce RAM jsnes. Code% attuale: b0 9.3%,
b1 13.7%, b2 6.7%, b3 1.8%, b4 2.7%, b5 2.1%, b6 5.8%, b7 59.3%.

## 6. Patch di prova (velocità di salto) e verifica dinamica

Costante: `src/bank7.s` ~$D6E8, `lda #$FB` (vy iniziale del salto; la
variante `#$FC` a ~$D6EE dipende dal bit0 di `$40`, parametro stage).

```sh
# 1. patch nel listing (l'indirizzo è nel commento di riga)
#    lda #$FB  ->  lda #$F8
make build/contra-rebuilt.nes
cmp -l "rom/Contra (USA).nes" build/contra-rebuilt.nes   # deve dare 1 byte
# 2. verifica in emulatore headless
cd tools/jsnes-test && npm i
node run.mjs ../../build/contra-rebuilt.nes script6.json
```

Lo script di test (già nel repo) preme START a f300, RIGHT da f750, A a f900
(byte joypad standard: A=$80, START=$10, RIGHT=$01 — attenzione: il campo
`p1` nei JSON è **decimale**). Output: `out.json` con RAM $0000-$07FF per
frame + screenshot PPM (convertire con ImageMagick `convert x.ppm x.png`).

Atteso con la patch: in `out.json`, al byte zp **`$C6`** (vy giocatore)
l'origale parte da `fb` e cresce `fc fd fe ff 00`, la patchata parte da `f8`;
a f915 lo screenshot mostra il giocatore a terra (originale) vs in cima allo
sky (patchato). Il gioco deve girare ~1000 frame senza crash.

Dopo l'esperimento: annullare la patch nel listing e `make verify` deve
tornare `IDENTICAL OK` (stato verde del repo).

## 7. Mappa repo

```
contra/
├── rom/Contra (USA).nes      SOLO locale, gitignored, fornito dall'utente
├── build/                    bank*.bin (da extract.sh), .o, contra-rebuilt.nes
├── src/
│   ├── header.s              header iNES 16B ricostruito (mapper 2, 8x16KB PRG, 0 CHR, mirror $21)
│   ├── symbols.inc           registri PPU/APU (emessi da da65 ASMINC)
│   └── bank0.s … bank7.s     listing ca65, ogni riga porta il suo dump hex
├── info/                     verità per da65: bankN.info (generati), bankN.ranges,
│                             seeds.txt (seed manuali), bankN.labels (label manuali)
├── tools/
│   ├── cc65/                 toolchain inclusa (git rimosso; build: make -C tools/cc65)
│   ├── extract.sh            ROM -> build/bankN.bin
│   ├── classify.py           code/data classifier
│   └── jsnes-test/           harness jsnes headless (run.mjs + scriptN.json)
├── link.cfg                  ld65: HEADER + 8 segmenti PRG -> %O
├── Makefile                  ranges -> info -> da65 -> ca65 -> ld65 -> verify
├── RAM.md                    mappa RAM $0000-$07FF (zp player, oggetti, sprite, enemy)
└── NOTES.md                  questo file
```

## 8. Architettura del gioco (annotazioni, per orientamento rapido)

Fatti verificati (listing + tracce jsnes); dettagli in `RAM.md` e nei
commenti dei listing.

- **Mapper 2 / UxROM**: `$8000-$BFFF` commutabile, `$C000-$FFFF` = banco 7
  fisso. Vettori: RESET=$C001, NMI=$C060, IRQ=$C0B5 (`rti`). Scrittura
  registro bank: `STA LFFD0,Y` (tabella id $FFD0). Salvataggio banco corrente
  in `$07EC`/`$07ED` tramite thunk `LC139/LC146/LC14C/LC15E`.
- **Main loop** ($C057): gira solo l'RNG (`$1A`+`$34`); tutta la logica è
  nell'NMI $C060 (fast-path su bit0 di `$1A`; shadow `$FF`/`$FE` = PPUCTRL/
  PPUMASK, in-game $B0/$B1).
- **Dispatcher stati** `$18` via `jsr LC857` con tabella word immediata
  inline (titolo $C25B … in-game $CE30). Sotto-stati `$2C`, tabella a $CE35
  (11 voci): $CE4B = init livello (copia 32 byte `$40-$5F` da
  `stage*32 + $B319`), $D02E = frame di gameplay.
- **Frame gameplay** (LCEF7) = 5 chiamate bancali: `LC1E9` (bank3 → $DC4B
  scroll engine), `LC1C9` (bank0 → $E61E enemy loop), `LC1D1`/`LC1E1`
  (bank2), `LC1F9` (bank2 → $CCB8).
- **Joypad** (`LC397`/`LC35B`): `$04/$05` raw, `$F1/$F2` held, `$F5/$F6`
  edge, `$F9/$FA` prev.
- **Player controller** (bank7 $D4xx-$E6xx), variabili zp per giocatore
  (X=0/1): `$32` vite (non `$90`, che è lo stato giocatore), `$AE` timer
  invincibilità, `$94/$96` posizione, `$98` subpixel X, `$9A` vx,
  `$A0` grounded, `$A4` pose, **`$C4` subpixel Y, `$C6` vy** (negativo = su,
  gravità +1/frame, landing azzera), `$BC` azione. Salto in `LD6D3`: sceglie
  vy iniziale `$FB` o `$FC` dal bit0 di `$40`.
- **Oggetti bank1**: 6 slot stride-6 in `$0100+X` (timer, tipo `$0106+X`,
  flags `$0124+X`, PC script `$0112/$0118`); `$012F` globale ferma tutto
  tranne il giocatore (tipo $54). Spawn da stream `LC8E3` → `LC9A3`.
  Sequencer SFX per oggetto scrive `SQ1_VOL,x`.
- **Sprite**: 26 slot SoA stride $1A in `$0300+X` (Y=$031A, X=$0334,
  meta=$034E), OAM shadow `$0200`, builder `LAE9D` (tabelle LB02E/LB12E).
- **Scrolling** ($DC4B): contatore 16-bit `$64/$65`, colonna `$60`, flip
  nametable `EOR #$01` su `$FF`, fine stage quando `$64 == $48`.
- **Enemy loop** bank0 $E61E: 16 slot `$04B8+X`, tipo `$0528+X` → jump
  table $E6A8 con dispatch indiretto `jmp ($04)`.

## 8b. Trucchi (God mode, 30 vite)

`make cheats` → `build/contra-god.nes`, `build/contra-30vite.nes` (gitignored).
Tabella in `tools/cheats.py`, identica a `CHEATS` in `nes/index.html` (dove
gli interruttori sul loader patchano la ROM in memoria prima di `loadROM`).

| Trucco | Indirizzo | Byte | Effetto |
|---|---|---|---|
| God | $E2C1 | B5→A9 | `lda $AE,x`→`lda #$AE`: il salto della collisione nemici/proiettili è sempre preso; niente lampeggio |
| God | $DA03 | D6→B5 | `dec $32,x`→`lda $32,x`: le cadute nei burroni non costano vite |
| 30 vite | $C462 | 02→1D | vite iniziali 29 (REST 30), stesso valore del codice Konami (`$24`) |

Verificati in jsnes headless (12000 frame camminando a destra): normale game
over a ~f3000; solo $E2C1 = niente morti da nemici ma i burroni uccidono;
God = vite ferme; 30 vite = REST 30 nell'intro dello stage 1.

## 9. Cosa non fare mai

- Non committare/pushare `*.nes`, `*.zip`, `build/prg.tmp`, dump RAM o
  screenshot presi dalla ROM se il repo diventa pubblico.
- Non "fixare" il `.gitignore` per far entrare la ROM.
- Non cancellare `tools/cc65/src/da65/comments.c` patchato.
- Non cambiare CPU da65 in `6502X` e non usare `;` nei file info.
- Non rendere `gen-info.sh` un target non-raggruppato (`&:`): con `-j` i file
  info si corrompono.
