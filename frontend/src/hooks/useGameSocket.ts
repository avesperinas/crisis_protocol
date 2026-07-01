import { useEffect, useRef } from 'react'

// Same idea as client.ts's BASE: in the production Docker build VITE_WS_BASE
// is set to "", and we fall back to building a same-origin ws(s):// URL from
// window.location so nginx's /ws/ proxy (see frontend/nginx.conf) can route it.
const configuredBase = import.meta.env.VITE_WS_BASE
const WS_BASE =
  configuredBase === undefined
    ? 'ws://127.0.0.1:8000'
    : configuredBase || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`

export type GameEvent =
  | { type: 'state_updated'; turn: number }
  | { type: 'action_submitted'; role_id: string }
  | { type: 'game_started' }
  | { type: 'lobby_updated' }

export function useGameSocket(
  gameId: string | undefined,
  roleId: string | undefined,
  onEvent: (event: GameEvent) => void,
) {
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    if (!gameId || !roleId) return

    let ws: WebSocket
    let reconnectTimer: ReturnType<typeof setTimeout>
    let heartbeatTimer: ReturnType<typeof setInterval>
    let alive = true

    const connect = () => {
      ws = new WebSocket(
        `${WS_BASE}/ws/games/${gameId}?role_id=${encodeURIComponent(roleId)}`,
      )

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data) as GameEvent
          onEventRef.current(data)
        } catch {
          // non-JSON message (e.g. "pong") — ignore
        }
      }

      ws.onopen = () => {
        heartbeatTimer = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, 25_000)
      }

      ws.onclose = () => {
        clearInterval(heartbeatTimer)
        if (alive) reconnectTimer = setTimeout(connect, 3_000)
      }
    }

    connect()

    return () => {
      alive = false
      clearTimeout(reconnectTimer)
      clearInterval(heartbeatTimer)
      ws?.close()
    }
  }, [gameId, roleId])
}
