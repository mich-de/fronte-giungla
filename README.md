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

Gioca a giochi NES nel browser. Per caricare una ROM:

1. Vai al link sopra.
2. Tocca il pulsante **"Carica ROM"** (o click su `[Carica]`).
3. Scegli un file `.nes` o `.zip` dal tuo dispositivo.
4. La ROM viene salvata in locale (IndexedDB) e ricaricata alla visita successiva.

**Comandi:**
- Frecce: movimento
- **Z**: B
- **X**: A
- **Invio**: Start
- **Shift**: Select
- **F**: schermo intero
- **%**: mostra/nascondi statistiche
