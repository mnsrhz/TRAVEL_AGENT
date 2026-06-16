export type WorkflowState =
  | "COLLECTING_REQUIREMENTS"
  | "AWAITING_PREFERENCE_APPROVAL"
  | "RESEARCHING"
  | "AWAITING_DESTINATION_APPROVAL"
  | "BUILDING_ITINERARY"
  | "REVIEWING"
  | "AWAITING_HIGH_RISK_DAY_APPROVAL"
  | "AWAITING_ITINERARY_APPROVAL"
  | "AWAITING_CALENDAR_APPROVAL"
  | "GENERATING_CALENDAR"
  | "COMPLETE"
  | "FAILED";

export type ChatMessage = {
  role: "assistant" | "user";
  content: string;
};

export type TraceEvent = {
  step: number;
  timestamp: string;
  state: WorkflowState;
  node: string;
  event_type: string;
  action: string;
  input_summary: string;
  output_summary: string;
  decision?: string | null;
  tokens_used: number;
  tool_calls_used: number;
  loop_count: number;
  max_loop_count: number;
  status: string;
  error?: string | null;
};

export type ItineraryEvent = {
  type: string;
  title: string;
  start: string;
  end: string;
  location: string;
  description?: string;
  cost?: string;
  source?: string;
};

export type ItineraryDay = {
  day: number;
  date: string;
  city: string;
  events: ItineraryEvent[];
};

export type TravelState = {
  user_input: Record<string, unknown>;
  preferences: Record<string, unknown>;
  destination_plan: Record<string, unknown>;
  flights: Array<Record<string, unknown>>;
  hotels: Array<Record<string, unknown>>;
  attractions: Array<Record<string, unknown>>;
  restaurants: Array<Record<string, unknown>>;
  transit_estimates: Array<Record<string, unknown>>;
  itinerary: ItineraryDay[];
  review: Record<string, unknown>;
  approvals: Record<string, boolean>;
  current_state: WorkflowState;
  tool_call_count: number;
  token_count: number;
  review_iteration_count: number;
  planner_iteration_count: number;
  trace_events: TraceEvent[];
  errors: string[];
  generated_ics?: string | null;
};

export type SessionResponse = {
  session_id: string;
  state: TravelState;
  chat_history: ChatMessage[];
};

export type ChatResponse = SessionResponse & {
  reply: string;
  ready: boolean;
};

