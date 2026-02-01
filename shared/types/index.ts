// Shared types between frontend and backend

export interface World {
  id: string;
  seed_prompt: string;
  config: WorldConfig;
  status: "created" | "running" | "paused" | "completed";
  current_epoch: number;
  current_tick: number;
  created_at: string;
}

export interface WorldConfig {
  era: string;
  tech_level: string;
  description: string;
  factions: FactionSpec[];
  constraints: string[];
}

export interface FactionSpec {
  name: string;
  description: string;
  color: string;
  agent_count: number;
}

export interface Agent {
  id: string;
  world_id: string;
  faction_id: string | null;
  name: string;
  persona: AgentPersona;
  beliefs: string[];
  status: "idle" | "speaking" | "listening" | "thinking";
}

export interface AgentPersona {
  name: string;
  role: string;
  personality: string;
  motivation: string;
  secret: string;
  speech_style: string;
}

export interface Relationship {
  id: string;
  world_id: string;
  agent_a: string;
  agent_b: string;
  type: "ally" | "rival" | "neutral" | "trade" | "mentor";
  strength: number;
}

export interface WSEnvelope {
  type: WSEventType;
  timestamp: string;
  epoch: number;
  payload: Record<string, unknown>;
}

export type WSEventType =
  | "agent.state"
  | "agent.message"
  | "relation.update"
  | "epoch.transition"
  | "event.triggered"
  | "wiki.edit"
  | "consensus.reached"
  | "herald.announcement";

export interface WikiPage {
  id: string;
  world_id: string;
  title: string;
  content: string;
  status: "draft" | "canon" | "legend" | "disputed";
  version: number;
  created_at: string;
}

export interface KnowledgeEdge {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
}
