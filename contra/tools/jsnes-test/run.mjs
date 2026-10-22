// Headless jsnes runner: loads ROM, feeds joypad input, dumps RAM snapshots.
// Usage: node run.js <rom> <script.json>
// script.json: { "frames": N, "input": {"<frame>": {"p1": 0xNN, "p2": 0xNN}}, "dump": [frames...] }
// Joypad bits (jsnes): A=1, B=2, SELECT=4, START=8, UP=16, DOWN=32, LEFT=64, RIGHT=128
import fs from "fs";
import { NES, Controller } from "jsnes";

const romPath = process.argv[2];
const scriptPath = process.argv[3];
const script = JSON.parse(fs.readFileSync(scriptPath, "utf8"));

const framebuffers = {};
let currentFrame = 0;

function onFrame(framebuffer) {
  if (script.screens && script.screens.includes(currentFrame)) {
    framebuffers[currentFrame] = Buffer.from(framebuffer);
  }
}

const nes = new NES({
  onFrame,
  onAudioSample: () => {},
});

const romData = fs.readFileSync(romPath);
nes.loadROM(romData);

function setController(player, buttons) {
  // Standard NES joypad byte: A=$80 B=$40 SELECT=$20 START=$10 UP=$08 DOWN=$04 LEFT=$02 RIGHT=$01
  const map = [
    [0x80, Controller.BUTTON_A],
    [0x40, Controller.BUTTON_B],
    [0x20, Controller.BUTTON_SELECT],
    [0x10, Controller.BUTTON_START],
    [0x08, Controller.BUTTON_UP],
    [0x04, Controller.BUTTON_DOWN],
    [0x02, Controller.BUTTON_LEFT],
    [0x01, Controller.BUTTON_RIGHT],
  ];
  for (const [bit, btn] of map) {
    if (buttons & bit) nes.buttonDown(player, btn);
    else nes.buttonUp(player, btn);
  }
}

const dumps = {};
const oams = {};
let dumpSet;
if (typeof script.dump === "string" && script.dump.startsWith("range:")) {
  const [a, b] = script.dump.slice(6).split("-").map(Number);
  dumpSet = new Set();
  for (let i = a; i <= b; i++) dumpSet.add(i);
} else {
  dumpSet = new Set(script.dump || []);
}
for (let f = 0; f < script.frames; f++) {
  currentFrame = f;
  const inp = script.input[String(f)];
  if (inp) {
    if (inp.p1 !== undefined) setController(1, inp.p1);
    if (inp.p2 !== undefined) setController(2, inp.p2);
  }
  nes.frame();
  if (dumpSet.has(f)) {
    dumps[f] = Array.from(nes.cpu.mem.slice(0, 0x800));
    oams[f] = Array.from(nes.ppu.spriteMem.slice(0, 256));
  }
}

const out = { dumps, oam: oams, frames: Object.keys(framebuffers).map(Number) };
fs.writeFileSync("out.json", JSON.stringify(out));
for (const [f, fb] of Object.entries(framebuffers)) {
  // jsnes framebuffer: 256*240 RGBA
  const w = 256, h = 240;
  const header = Buffer.from(`P6\n${w} ${h}\n255\n`);
  const rgb = Buffer.alloc(w * h * 3);
  const stride = fb.length >= w * h * 4 ? 4 : 1;
  for (let i = 0; i < w * h; i++) {
    rgb[i * 3] = fb[i * stride];
    rgb[i * 3 + 1] = fb[i * stride + (stride === 4 ? 1 : 0)];
    rgb[i * 3 + 2] = fb[i * stride + (stride === 4 ? 2 : 0)];
  }
  fs.writeFileSync(`screen-${f}.ppm`, Buffer.concat([header, rgb]));
}
console.log("done", Object.keys(dumps));
