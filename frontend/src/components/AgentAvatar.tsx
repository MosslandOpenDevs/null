"use client";

const SIZE_MAP = {
  sm: "w-5 h-5 text-[9px]",
  md: "w-7 h-7 text-[11px]",
  lg: "w-9 h-9 text-sm",
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
