import { create } from "zustand";

interface AudioState {
  audioEnabled: boolean;
  ambientCleanup: (() => void) | null;
  toggleAudio: () => void;
  startAmbient: () => Promise<void>;
  stopAmbient: () => void;
  playChime: () => void;
  playEpochTransition: () => void;
  playConflictTone: () => void;
  playAllianceTone: () => void;
}

let toneImport: typeof import("tone") | null = null;

async function getTone() {
  if (!toneImport) {
    toneImport = await import("tone");
  }
  return toneImport;
}

export const useAudioStore = create<AudioState>((set, get) => ({
  audioEnabled: false,
  ambientCleanup: null,

  toggleAudio: () => {
    const { audioEnabled, startAmbient, stopAmbient } = get();
    if (audioEnabled) {
      stopAmbient();
    } else {
      startAmbient();
    }
    set({ audioEnabled: !audioEnabled });
  },

  startAmbient: async () => {
    const Tone = await getTone();
    await Tone.start();

    const synth = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: "sine" },
      envelope: { attack: 2, decay: 1, sustain: 0.3, release: 4 },
      volume: -20,
    }).toDestination();

    const notes = ["C2", "E2", "G2", "B2"];
    const loop = new Tone.Loop((time) => {
      const note = notes[Math.floor(Math.random() * notes.length)];
      synth.triggerAttackRelease(note, "4n", time);
    }, "2n");

    loop.start(0);
    Tone.getTransport().start();

    const cleanup = () => {
      loop.stop();
      Tone.getTransport().stop();
      synth.dispose();
    };

    set({ ambientCleanup: cleanup });
  },

  stopAmbient: () => {
    const { ambientCleanup } = get();
    ambientCleanup?.();
    set({ ambientCleanup: null });
  },

  playChime: async () => {
    if (!get().audioEnabled) return;
    const Tone = await getTone();
    await Tone.start();
    const synth = new Tone.Synth({
      oscillator: { type: "triangle" },
      envelope: { attack: 0.01, decay: 0.3, sustain: 0, release: 0.5 },
      volume: -15,
    }).toDestination();
    synth.triggerAttackRelease("C5", "8n");
    setTimeout(() => synth.dispose(), 1000);
  },

  playEpochTransition: async () => {
    if (!get().audioEnabled) return;
    const Tone = await getTone();
    await Tone.start();
    const synth = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: "sine" },
      envelope: { attack: 0.5, decay: 1, sustain: 0.2, release: 2 },
      volume: -12,
    }).toDestination();
    synth.triggerAttackRelease(["C3", "E3", "G3"], "2n");
    setTimeout(() => synth.dispose(), 3000);
  },

  playConflictTone: async () => {
    if (!get().audioEnabled) return;
    const Tone = await getTone();
    await Tone.start();
    const synth = new Tone.Synth({
      oscillator: { type: "sawtooth" },
      envelope: { attack: 0.05, decay: 0.3, sustain: 0.1, release: 0.5 },
      volume: -18,
    }).toDestination();
    synth.triggerAttackRelease("Eb3", "8n");
    setTimeout(() => {
      synth.triggerAttackRelease("D3", "8n");
    }, 150);
    setTimeout(() => synth.dispose(), 1000);
  },

  playAllianceTone: async () => {
    if (!get().audioEnabled) return;
    const Tone = await getTone();
    await Tone.start();
    const synth = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: "triangle" },
      envelope: { attack: 0.1, decay: 0.3, sustain: 0.1, release: 0.8 },
      volume: -15,
    }).toDestination();
    synth.triggerAttackRelease(["C4", "E4", "G4"], "4n");
    setTimeout(() => synth.dispose(), 1500);
  },
}));
