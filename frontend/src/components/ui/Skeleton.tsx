"use client";

import clsx from "clsx";

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export function Skeleton({ className, lines = 1 }: SkeletonProps) {
  return (
    <div className={clsx("space-y-2", className)}>
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className="h-4 rounded-sm animate-cosmic-shimmer"
          style={{ width: `${80 + Math.random() * 20}%` }}
        />
      ))}
    </div>
  );
}

export function ChronicleBlockSkeleton() {
  return (
    <div className="w-full px-4 py-3 border border-hud-border/30 rounded-sm space-y-2">
      <div className="flex items-center gap-2">
        <div className="h-3 w-16 animate-cosmic-shimmer rounded-sm" />
        <div className="h-3 w-24 animate-cosmic-shimmer rounded-sm" />
      </div>
      <Skeleton lines={3} />
      <div className="flex gap-2">
        <div className="h-5 w-20 animate-cosmic-shimmer rounded-sm" />
        <div className="h-5 w-16 animate-cosmic-shimmer rounded-sm" />
      </div>
    </div>
  );
}

export function MinimapSkeleton() {
  return (
    <div className="space-y-3 px-3 py-3">
      {/* Graph skeleton */}
      <div className="w-full h-48 animate-cosmic-shimmer rounded-sm" />
      {/* Power bar skeleton */}
      <div className="h-3 animate-cosmic-shimmer rounded-sm" />
      {/* Agent list skeleton */}
      <div className="space-y-1">
        {Array.from({ length: 5 }, (_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full animate-cosmic-shimmer" />
            <div className="h-3 flex-1 animate-cosmic-shimmer rounded-sm" />
          </div>
        ))}
      </div>
    </div>
  );
}
