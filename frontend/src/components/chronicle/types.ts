export type ChronicleItemType = "herald" | "conversation" | "wiki" | "event" | "epoch";

export interface HeraldItem {
  type: "herald";
  id: string;
  epoch: number;
  tick: number;
  timestamp: string;
  text: string;
}

export interface ConversationItem {
  type: "conversation";
  id: string;
  epoch: number;
  tick: number;
  timestamp: string;
  topic: string;
  participants: Array<{ id: string; name: string; faction_id: string | null; faction_color: string }>;
  messages: Array<{ agent_id: string; agent_name: string; content: string; faction_color: string }>;
  summary?: string;
}

export interface WikiItem {
  type: "wiki";
  id: string;
  epoch: number;
  tick: number;
  timestamp: string;
  title: string;
  content: string;
  version: number;
  referencingAgents?: number;
  disputes?: number;
}

export interface EventItem {
  type: "event";
  id: string;
  epoch: number;
  tick: number;
  timestamp: string;
  eventType: "crisis" | "discovery" | "plague" | "leadership" | "general";
  description: string;
  affectedAgents?: string[];
}

export interface EpochItem {
  type: "epoch";
  id: string;
  epoch: number;
  timestamp: string;
  summary?: string;
  dominantTheme?: "prosperity" | "conflict" | "discovery" | "transition";
}

export type ChronicleItem = HeraldItem | ConversationItem | WikiItem | EventItem | EpochItem;
