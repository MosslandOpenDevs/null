import { create } from "zustand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export interface BookmarkData {
  id: string;
  user_session: string;
  label: string;
  entity_type: string;
  entity_id: string;
  world_id: string;
  note: string;
  created_at: string;
}

function getSession(): string {
  if (typeof window === "undefined") return "anonymous";
  let session = localStorage.getItem("null_session");
  if (!session) {
    session = Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("null_session", session);
  }
  return session;
}

interface BookmarkState {
  bookmarks: BookmarkData[];
  drawerOpen: boolean;

  fetchBookmarks: () => Promise<void>;
  addBookmark: (entity_type: string, entity_id: string, world_id: string, label: string, note?: string) => Promise<void>;
  removeBookmark: (id: string) => Promise<void>;
  exportBookmarks: () => Promise<void>;
  setDrawerOpen: (open: boolean) => void;
}

export const useBookmarkStore = create<BookmarkState>((set, get) => ({
  bookmarks: [],
  drawerOpen: false,

  fetchBookmarks: async () => {
    try {
      const session = getSession();
      const resp = await fetch(`${API_URL}/api/bookmarks?session=${encodeURIComponent(session)}`);
      if (resp.ok) {
        const bookmarks = await resp.json();
        set({ bookmarks });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  addBookmark: async (entity_type, entity_id, world_id, label, note = "") => {
    try {
      const session = getSession();
      const resp = await fetch(`${API_URL}/api/bookmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_session: session, entity_type, entity_id, world_id, label, note }),
      });
      if (resp.ok) {
        await get().fetchBookmarks();
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  removeBookmark: async (id) => {
    try {
      await fetch(`${API_URL}/api/bookmarks/${id}`, { method: "DELETE" });
      set((s) => ({ bookmarks: s.bookmarks.filter((b) => b.id !== id) }));
    } catch {
      // endpoint may not exist yet
    }
  },

  exportBookmarks: async () => {
    try {
      const session = getSession();
      const resp = await fetch(`${API_URL}/api/bookmarks/export?session=${encodeURIComponent(session)}`, {
        method: "POST",
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "bookmarks.json";
        a.click();
        URL.revokeObjectURL(a.href);
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  setDrawerOpen: (open) => set({ drawerOpen: open }),
}));
