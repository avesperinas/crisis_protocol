export type Posture = 'confrontational' | 'cooperative' | 'ambiguous'
export type Domain = 'MIL' | 'DIP' | 'ECO' | 'INT'

export interface TokenAllocation {
  MIL: number
  DIP: number
  ECO: number
  INT: number
}

export interface FactionInfo {
  id: string
  name: string
  tagline: string
  description: string
  starting_resources: TokenAllocation
  token_budget_per_turn: number
}

export type PactType = 'alliance' | 'non_aggression' | 'trade' | 'intel_share'

export interface PactTypeLabel {
  label: string
  help: string
}

export type PactTypeLabels = Record<PactType, PactTypeLabel>

export interface ScenarioInfo {
  id: string
  name: string
  year: string
  type: string
  max_turns: number
  example_directive: string
  pact_type_labels: PactTypeLabels
  factions: FactionInfo[]
}

export interface GameCreatedResponse {
  game_id: string
  your_role_id: string
  user_token: string
  join_code: string | null
  mode: string
}

export interface LobbySlot {
  role_id: string
  role_name: string
  tagline: string
  is_taken: boolean
  is_human: boolean
}

export interface LobbyStateView {
  game_id: string
  join_code: string
  room_name: string | null
  scenario_id: string
  scenario_name: string
  async_mode: boolean
  slots: LobbySlot[]
  is_started: boolean
  is_host: boolean
  connected_roles: string[]
}

export interface FactionView {
  id: string
  name: string
  tagline: string
  public_objective: string
}

export interface PlayerView {
  role_id: string
  role_name: string
  tagline: string
  is_ai: boolean
  is_you: boolean
  briefing: string | null
  resources: TokenAllocation | null
  token_budget_per_turn: number | null
  public_objective_text: string | null
  hidden_objective_text: string | null
}

export interface ResolvedActionView {
  role_id: string
  posture: Posture
  directive: string | null
  coherence_score: number | null
  decision_quality: number | null
  effective_multiplier: number | null
  action_type: string | null
  target_id: string | null
}

export interface TurnView {
  turn_number: number
  max_turns: number
  status: 'collecting' | 'resolving' | 'finished'
  tension_at_start: number
  tension_at_end: number | null
  narrative: string | null
  intel_for_you: string | null
  your_action_submitted: boolean
  humans_submitted: number
  humans_total: number
  resolved_actions: ResolvedActionView[]
}

export interface PactView {
  id: string
  type: PactType
  player_a_id: string
  player_b_id: string
  is_secret: boolean
  is_active: boolean
  created_turn: number
}

export interface MessageView {
  id: string
  turn_number: number
  from_role_id: string
  to_role_id: string | null
  content: string
  is_proposal: boolean
  proposal_type: string | null
  proposal_status: string | null
  created_at: string
}

export interface GameStateView {
  game_id: string
  scenario_id: string
  scenario_name: string
  status: 'lobby' | 'briefing' | 'active' | 'resolving' | 'finished'
  current_turn: number
  max_turns: number
  tension: number
  your_role_id: string
  example_directive: string
  pact_type_labels: PactTypeLabels
  factions: FactionView[]
  you: PlayerView
  active_pacts: PactView[]
  messages: MessageView[]
  current_turn_view: TurnView | null
  previous_turn_view: TurnView | null
}

export interface PactProposalResult {
  status: 'accepted' | 'rejected' | 'pending'
  accepted: boolean
  pact_id: string | null
  proposal_message_id: string
  reason: string
}

export interface PactBreakResult {
  pact_id: string
  new_tension: number
  breaker_dip_after: number
}

export interface ActionSubmission {
  posture: Posture
  tokens: TokenAllocation
  directive: string
}

export interface ActionSubmittedResponse {
  accepted: boolean
  turn_resolved: boolean
  message: string
}

export interface ScoreBreakdownView {
  objective: number
  efficiency: number
  capital: number
  decision_quality: number
  total: number
}

export interface ScoreboardEntry {
  role_id: string
  role_name: string
  is_human: boolean
  score: ScoreBreakdownView
  public_objective_met: boolean
  hidden_objective_met: boolean
  public_objective_text: string
  hidden_objective_text: string
}

export interface FinalResultView {
  game_id: string
  scenario_id: string
  scenario_name: string
  final_tension: number
  final_narrative: string | null
  scoreboard: ScoreboardEntry[]
}
