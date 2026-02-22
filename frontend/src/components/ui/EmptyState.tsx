"use client";

interface EmptyStateProps {
  message?: string;
  submessage?: string;
}

export function EmptyState({
  message = "THE VOID AWAITS",
  submessage = "No data to display yet",
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px] gap-2">
      <div className="font-mono text-base text-hud-muted animate-pulse-glow">
        {message}
      </div>
      <div className="font-mono text-sm text-hud-label">
        {submessage}
      </div>
    </div>
  );
}
