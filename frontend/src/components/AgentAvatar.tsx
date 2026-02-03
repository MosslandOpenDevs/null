"use client";

const SIZE_MAP = {
  sm: "w-6 h-6 text-xs",
  md: "w-8 h-8 text-sm",
  lg: "w-10 h-10 text-base",
} as const;

const FALLBACK_COLORS = [
  "#4f46e5", "#db2777", "#0d9488", "#d97706", "#7c3aed",
  "#dc2626", "#059669", "#0891b2", "#ea580c", "#9333ea",
];

function hashColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return FALLBACK_COLORS[Math.abs(hash) % FALLBACK_COLORS.length];
}

interface AgentAvatarProps {
  name: string;
  factionColor?: string | null;
  size?: "sm" | "md" | "lg";
}

export function AgentAvatar({ name, factionColor, size = "md" }: AgentAvatarProps) {
  const color = factionColor || hashColor(name);
  const initial = name.charAt(0).toUpperCase();

  return (
    <div
      className={`${SIZE_MAP[size]} rounded-full flex items-center justify-center font-sans font-bold flex-shrink-0`}
      style={{ backgroundColor: color + "18", color }}
      title={name}
    >
      {initial}
    </div>
  );
}
