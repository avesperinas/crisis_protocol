export interface AuthUser {
  id: string
  email: string
  username: string
  locale: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
}
