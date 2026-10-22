# Fronte Giungla

Run-and-gun a scorrimento in stile 8-bit, ispirato a Contra (NES), giocabile nel browser da telefono e da PC.
Grafica, musica ed effetti sono originali e generati nel codice: un unico file `index.html`, senza dipendenze.

**Gioca:** https://mich-de.github.io/fronte-giungla/

## Comandi

| | Telefono | Tastiera |
|---|---|---|
| Muovi e mira (8 direzioni) | levetta a sinistra | frecce / WASD |
| Spara | B | X / J |
| Salta | A | Z / K / Spazio |
| Scendi dalla piattaforma | giù + A | giù + Z |
| Pausa | II | P / Esc |
| Schermo intero | ⛶ (automatico al primo tocco) | F |

Armi: **M** mitragliatrice, **S** ventaglio, **L** laser, **R** colpi più veloci, **B** scudo temporaneo.
Meglio con il telefono in orizzontale.

## God mode (debug)

Nella schermata iniziale scegli **GOD MODE (DEBUG)** con su/giù (o toccandolo) e conferma con B / X.
Il giocatore è invulnerabile, il record non viene salvato e compaiono gli strumenti di debug:

- riga in basso con posizione, camera, nemici, proiettili e FPS
- **W** / tasto `C`: cambia arma (N → M → S → L)
- **»** / tasto `V`: salta avanti di 400 px nel livello

## NES Emulator

**Emulatore NES:** https://mich-de.github.io/fronte-giungla/nes/

Gioca a giochi NES nel browser. Le ROM stanno in una **cartucciera**: uno scaffale di cartucce salvate sul dispositivo (IndexedDB), mai caricate online.

1. Vai al link sopra.
2. Tocca **+ AGGIUNGI** e scegli uno o più file `.nes` o `.zip`.
3. Tocca una cartuccia per inserirla, toccala di nuovo (o premi **GIOCA**) per giocare. **⏏** torna alla cartucciera.
4. **TOGLI CARTUCCIA** la elimina insieme ai suoi salvataggi. Con un controller: sinistra/destra per scegliere, START o A per giocare.

**Comandi:**

| | Telefono | Controller USB/Bluetooth | Tastiera |
|---|---|---|---|
| Direzioni | croce del controller NES a schermo (8 direzioni, si può scorrere) | croce o levetta sinistra | frecce |
| B / A | pulsanti rossi; dito in mezzo ai due = entrambi | tasti sinistro/basso = B, destro/alto = A | Z / X |
| Select / Start | SELECT / START | Select / Start | Shift / Invio |
| Schermo intero | ⛶ | | F |

- A schermo c'è un controller NES (scocca grigia, frontale nero): sotto lo schermo in verticale, diviso in due metà ai lati in orizzontale.
- Controller fisico: collegalo e premi un tasto. I comandi a schermo spariscono e tornano al primo tocco. Con due controller si gioca in due (es. Contra in cooperativa). **A⇄B** scambia i tasti se il controller li ha invertiti. Nel menu, START o A avvia il gioco.
- **TB**: turbo su B. **SAV / LOAD**: salvataggio di stato.
- **Trucchi per Contra (USA)**: con questa ROM caricata, nel menu compaiono **GOD MODE** (invincibile a nemici e proiettili, le cadute non costano vite) e **30 VITE**. Si attivano prima di premere GIOCA. I salvataggi di stato sono separati per ogni combinazione di trucchi.
