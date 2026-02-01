let toneImport: typeof import("tone") | null = null;

async function getTone() {
  if (!toneImport) {
    toneImport = await import("tone");
  }
  return toneImport;
}

export async function playAmbient() {
  const Tone = await getTone();
  await Tone.start();

  const synth = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type: "sine" },
    envelope: { attack: 2, decay: 1, sustain: 0.3, release: 4 },
    volume: -20,
  }).toDestination();

  // Ambient drone
  const notes = ["C2", "E2", "G2", "B2"];
  const loop = new Tone.Loop((time) => {
    const note = notes[Math.floor(Math.random() * notes.length)];
    synth.triggerAttackRelease(note, "4n", time);
  }, "2n");

  loop.start(0);
  Tone.getTransport().start();

  return () => {
    loop.stop();
    Tone.getTransport().stop();
    synth.dispose();
  };
}

export async function playEventChime() {
  const Tone = await getTone();
  await Tone.start();

  const synth = new Tone.Synth({
    oscillator: { type: "triangle" },
    envelope: { attack: 0.01, decay: 0.3, sustain: 0, release: 0.5 },
    volume: -15,
  }).toDestination();

  synth.triggerAttackRelease("C5", "8n");
  setTimeout(() => synth.dispose(), 1000);
}
