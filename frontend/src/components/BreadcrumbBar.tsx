"use client";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbBarProps {
  items: BreadcrumbItem[];
}

export function BreadcrumbBar({ items }: BreadcrumbBarProps) {
  if (items.length === 0) return null;

  return (
    <nav className="flex items-center gap-1 px-3 py-1.5 border-b border-hud-border bg-void-light/50">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && (
            <span className="font-mono text-xs text-hud-label">›</span>
          )}
          {item.href ? (
            <a
              href={item.href}
              className="font-mono text-xs text-hud-muted hover:text-accent uppercase tracking-wider transition-colors"
            >
              {item.label}
            </a>
          ) : (
            <span className="font-mono text-xs text-hud-text uppercase tracking-wider">
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}
