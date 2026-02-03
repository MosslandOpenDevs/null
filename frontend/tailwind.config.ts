import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        void: "#faf9f6",
        "void-light": "#f5f4f0",
        "void-alt": "#eeece6",
        accent: "#4f46e5",
        herald: "#d97706",
        danger: "#dc2626",
        success: "#059669",
        warning: "#d97706",
        cyan: "#0891b2",
        "hud-border": "#d4d2ca",
        "hud-border-active": "#a8a69d",
        "hud-text": "#3d3b37",
        "hud-muted": "#6b6863",
        "hud-label": "#9d9a92",
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
