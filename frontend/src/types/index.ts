export interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  data?: any[];
  sqlQuery?: string;
  matchedPlayers?: string[];
  executionTime?: number;
  isLoading?: boolean;
}

export interface ChatResponse {
  response: string;
  data?: any[];
  sql_query?: string;
  matched_players?: string[];
  execution_time?: number;
}

export interface PlayerSuggestion {
  name: string;
  confidence: number;
}

export interface QueryValidation {
  valid: boolean;
  sql_query?: string;
  matched_players?: string[];
  query_type?: string;
}

export interface SummaryStats {
  total_matches: number;
  total_batters: number;
  total_bowlers: number;
  total_venues: number;
  total_seasons: number;
  earliest_date: string;
  latest_date: string;
  total_balls: number;
}