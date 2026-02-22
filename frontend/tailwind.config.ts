import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        void: "#0a0a0f",
        "void-light": "#111118",
        "void-alt": "#1a1a24",
        accent: "#4f46e5",
        herald: "#d97706",
        danger: "#dc2626",
        success: "#059669",
        warning: "#d97706",
        cyan: "#0891b2",
        "hud-border": "#2a2a3a",
        "hud-border-active": "#3d3d52",
        "hud-text": "#e0dfd8",
        "hud-muted": "#8888a0",
        "hud-label": "#6a6a80",
        "glow-blue": "#4488ff",
        "glow-red": "#ff4466",
        "glow-gold": "#ffaa33",
        "glow-green": "#33ff88",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
        serif: ["Source Serif Pro", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
