// Types aligned with FastAPI backend

export interface User {
  id: string;
  email: string;
  grade_level: number | null;
  created_at: string;
}

export interface UserProfile {
  user_id: string;
  topic_mastery: Record<string, number>;
  concept_dependency_map: Record<string, unknown>;
  misconception_patterns: Record<string, unknown>[];
  learning_speed: number;
  retention_strength: number;
  error_recurrence_rate: number;
  cognitive_load_tolerance: number;
  response_preference: string;
  hint_dependency_level: number;
  step_by_step_preference: number;
  weak_topics: string[];
  strong_topics: string[];
  updated_at: string;
}

export interface SessionItem {
  id: string;
  user_id: string;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  topics_covered: string[];
  last_message: string | null;
}

export interface MessageItem {
  id: string;
  query: string;
  response: string;
  created_at: string;
}

export interface SessionDetail {
  id: string;
  user_id: string;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  topics_covered: string[];
  messages: MessageItem[];
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  response: string;
  teaching_strategy_used: string;
  bloom_level: string;
  topics_covered: string[];
  sources: ChunkReference[];
  follow_up_suggestions: string[];
}

export interface ChunkReference {
  chunk_id: string;
  article_title: string;
  section_header: string | null;
}

export interface WikiChunk {
  id: number;
  chunk_id: string;
  title: string;
  content: string;
  subject: string | null;
  subject_vn: string | null;
  grade: number | null;
  topic: string | null;
  source: string | null;
  chunk_type: string | null;
  section: string | null;
  has_formula: boolean;
  length: number | null;
}
