import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        void: "#06060b",
        "void-light": "#0c0c14",
        "void-alt": "#111119",
        accent: "#6366f1",
        herald: "#f59e0b",
        danger: "#ef4444",
        success: "#22c55e",
        warning: "#f59e0b",
        cyan: "#22d3ee",
        "hud-border": "#1a1a2e",
        "hud-border-active": "#2a2a4e",
        "hud-text": "#c8c8d4",
        "hud-muted": "#5a5a6e",
        "hud-label": "#3a3a4e",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
