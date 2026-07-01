export interface UserSearchResult {
  id: string
  username: string
}

export interface FriendEntry {
  friendship_id: string
  user_id: string
  username: string
  status: 'pending' | 'accepted'
  direction: 'incoming' | 'outgoing' | 'mutual'
}

export interface InviteEntry {
  id: string
  from_username: string
  game_id: string
  join_code: string
  room_name: string | null
  scenario_name: string
}

export interface FriendsListView {
  friends: FriendEntry[]
  invites: InviteEntry[]
}

export interface GameHistoryEntry {
  game_id: string
  scenario_id: string
  scenario_name: string
  role_id: string
  role_name: string
  finished_at: string | null
  score_total: number
  rank: number
  player_count: number
  public_objective_met: boolean
  hidden_objective_met: boolean
}

export interface UserStats {
  games_played: number
  wins: number
  favorite_scenario: string | null
  favorite_faction: string | null
  avg_decision_quality: number
  avg_coherence: number
  public_objective_rate: number
  hidden_objective_rate: number
}
