"use client";

import { useParams, usePathname } from "next/navigation";

export function LocaleToggle() {
  const { locale } = useParams<{ locale: string }>();
  const pathname = usePathname();

  const otherLocale = locale === "ko" ? "en" : "ko";
  // Replace /{locale}/ prefix in pathname
  const newPath = pathname.replace(`/${locale}`, `/${otherLocale}`);

  return (
    <a
      href={newPath}
      className="flex items-center gap-1.5 px-3 py-1.5 border border-hud-border hover:border-accent bg-void-light/80 rounded font-mono text-xs text-hud-muted hover:text-accent transition-colors"
      title={locale === "ko" ? "Switch to English" : "한국어로 전환"}
    >
      <span className={locale === "ko" ? "text-hud-muted" : "text-accent font-semibold"}>EN</span>
      <span className="text-hud-label">/</span>
      <span className={locale === "ko" ? "text-accent font-semibold" : "text-hud-muted"}>한</span>
    </a>
  );
}
