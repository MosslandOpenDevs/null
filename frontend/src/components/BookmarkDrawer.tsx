"use client";

import { useEffect, useMemo } from "react";
import { useBookmarkStore } from "@/stores/bookmarks";

export function BookmarkDrawer() {
  const {
    bookmarks,
    drawerOpen,
    setDrawerOpen,
    fetchBookmarks,
    removeBookmark,
    exportBookmarks,
  } = useBookmarkStore();

  const hasBookmarks = bookmarks.length > 0;
  const canExport = drawerOpen && hasBookmarks;

  useEffect(() => {
    if (drawerOpen) {
      fetchBookmarks();
    }
  }, [drawerOpen, fetchBookmarks]);

  const footerText = useMemo(() => (hasBookmarks ? `${bookmarks.length} BOOKMARKS` : "No bookmarks yet"), [bookmarks.length, hasBookmarks]);

  if (!drawerOpen) return null;

  return (
    <div className="fixed right-0 top-0 bottom-0 w-80 z-50 bg-void-light border-l border-hud-border flex flex-col shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-hud-border">
        <h2 className="font-mono text-base text-hud-text uppercase tracking-[0.15em]">
          BOOKMARKS
        </h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={exportBookmarks}
            disabled={!hasBookmarks}
            className={`font-mono text-sm uppercase tracking-wider ${
              hasBookmarks ? "text-accent hover:text-accent/80" : "text-hud-label cursor-not-allowed"
            }`}
            title={hasBookmarks ? "Download bookmarks JSON" : "No bookmarks to export"}
            aria-label={hasBookmarks ? "Export bookmarks" : "Export unavailable: no bookmarks"}
          >
            EXPORT
          </button>
          <button
            type="button"
            onClick={() => setDrawerOpen(false)}
            className="font-mono text-[13px] text-hud-muted hover:text-danger"
            aria-label="Close bookmark drawer"
          >
            ✕
          </button>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {bookmarks.length === 0 ? (
          <div className="font-mono text-[13px] text-hud-label text-center py-8">
            NO BOOKMARKS YET
          </div>
        ) : (
          bookmarks.map((bm) => (
            <div
              key={bm.id}
              className="p-2 border border-hud-border hover:border-hud-border-active transition-colors"
            >
              <div className="flex items-center justify-between">
                <a
                  href={`/en/world/${bm.world_id}`}
                  className="font-mono text-[13px] text-hud-text hover:text-accent truncate flex-1"
                >
                  {bm.label || bm.entity_type}
                </a>
                <button
                  type="button"
                  onClick={() => removeBookmark(bm.id)}
                  className="font-mono text-[11px] text-hud-muted hover:text-danger ml-2 flex-shrink-0"
                  aria-label={`Remove bookmark for ${bm.label || bm.entity_type}`}
                >
                  DEL
                </button>
              </div>
              <div className="font-mono text-[11px] text-hud-label mt-0.5">
                {bm.entity_type.replace("_", " ")}
              </div>
              {bm.note && (
                <div className="font-mono text-[11px] text-hud-muted mt-0.5 truncate">
                  {bm.note}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-hud-border">
        <div className="font-mono text-[11px] text-hud-label">{footerText}</div>
      </div>

      <div className="sr-only" aria-live="polite">
        {canExport ? `Bookmark drawer open, ${bookmarks.length} bookmarks` : "Bookmark drawer open, no bookmarks"}
      </div>
    </div>
  );
}
