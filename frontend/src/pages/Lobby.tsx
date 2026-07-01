import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { FactionBadge } from '../components/FactionBadge'
import { useGameStore } from '../store/gameStore'
import { factionTheme } from '../theme/factions'
import type { LobbyStateView, ScenarioInfo } from '../types/game'

type Tab = 'solo' | 'join' | 'create-multi'

export function Lobby() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const setSession = useGameStore((s) => s.setSession)
  const session = useGameStore((s) => s.session)

  const prefillJoinCode = searchParams.get('join') ?? ''
  const [tab, setTab] = useState<Tab>(prefillJoinCode ? 'join' : 'solo')
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([])
  const [scenarioId, setScenarioId] = useState<string>('corinth_338')
  const [roleId, setRoleId] = useState<string>('')
  const [roomName, setRoomName] = useState<string>('')
  const [asyncMode, setAsyncMode] = useState(false)
  const [joinCode, setJoinCode] = useState<string>(prefillJoinCode)
  const [joinRoleId, setJoinRoleId] = useState<string>('')
  const [joinPreview, setJoinPreview] = useState<LobbyStateView | null>(null)
  const [joinLookupError, setJoinLookupError] = useState<string | null>(null)
  const [joinLookupLoading, setJoinLookupLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listScenarios()
      .then((s) => {
        setScenarios(s)
        if (s[0]) {
          setScenarioId(s[0].id)
          setRoleId(s[0].factions[0]?.id ?? '')
          setJoinRoleId(s[0].factions[0]?.id ?? '')
        }
      })
      .catch((e) => setError(String(e)))
  }, [])

  // Look up the room's actual scenario/slots as soon as a full code is typed —
  // the join-by-code faction picker must reflect the target room, not whatever
  // scenario happens to be selected in the other tabs.
  useEffect(() => {
    const code = joinCode.trim().toUpperCase()
    if (code.length !== 6) {
      setJoinPreview(null)
      setJoinLookupError(null)
      setJoinRoleId('')
      return
    }
    setJoinLookupLoading(true)
    const handle = setTimeout(() => {
      api
        .getLobbyByCode(code)
        .then((lobby) => {
          setJoinPreview(lobby)
          setJoinLookupError(null)
          const firstFree = lobby.slots.find((s) => !s.is_taken)
          setJoinRoleId(firstFree?.role_id ?? '')
        })
        .catch((e) => {
          setJoinPreview(null)
          setJoinLookupError(String(e))
        })
        .finally(() => setJoinLookupLoading(false))
    }, 400)
    return () => clearTimeout(handle)
  }, [joinCode])

  const scenario = scenarios.find((s) => s.id === scenarioId)
  const selectedFaction = scenario?.factions.find((f) => f.id === roleId)

  const createSolo = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.createGame(scenarioId, roleId, 'solo')
      setSession({ gameId: res.game_id, roleId: res.your_role_id, userToken: res.user_token })
      navigate(`/games/${res.game_id}/briefing`)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const createMulti = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.createGame(scenarioId, roleId, 'multiplayer', roomName, asyncMode)
      setSession({ gameId: res.game_id, roleId: res.your_role_id, userToken: res.user_token })
      navigate(`/games/${res.game_id}/waiting`)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const joinByCode = async () => {
    if (!joinCode.trim() || !joinRoleId) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.joinGame(joinCode.trim().toUpperCase(), joinRoleId)
      setSession({ gameId: res.game_id, roleId: res.your_role_id, userToken: res.user_token })
      navigate(`/games/${res.game_id}/waiting`)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex-1 flex flex-col justify-center">
      <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-4 w-full">
      <header>
        <h1>{t('lobby.title')}</h1>
        <p className="text-neutral-600 mt-1">{t('lobby.subtitle')}</p>
      </header>

      {session && (
        <div className="card text-sm">
          {t('lobby.sessionInProgress')}{' '}
          <span className="font-mono">{session.gameId.slice(0, 8)}</span> {t('lobby.asLabel')}{' '}
          <span className="font-medium">{session.roleId}</span>.{' '}
          <button
            className="underline"
            onClick={() => navigate(`/games/${session.gameId}/game`)}
          >
            {t('lobby.continueBtn')}
          </button>{' '}
          ·{' '}
          <button className="underline" onClick={() => setSession(null)}>
            {t('lobby.forgetBtn')}
          </button>
        </div>
      )}

      <div className="flex gap-1 border-b border-neutral-200">
        {(
          [
            { key: 'solo', label: t('lobby.tabSolo') },
            { key: 'create-multi', label: t('lobby.tabCreateMulti') },
            { key: 'join', label: t('lobby.tabJoin') },
          ] as { key: Tab; label: string }[]
        ).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => { setTab(key); setError(null) }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? 'border-slate-700 text-slate-800'
                : 'border-transparent text-neutral-500 hover:text-neutral-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {(tab === 'solo' || tab === 'create-multi') && (
        <section className="card md:flex md:gap-6 md:items-start">
          <div className="flex-1 min-w-0 space-y-4">
            <div>
              <label className="label block mb-1">{t('lobby.scenarioLabel')}</label>
              <select
                className="input"
                value={scenarioId}
                onChange={(e) => {
                  setScenarioId(e.target.value)
                  const s = scenarios.find((sc) => sc.id === e.target.value)
                  setRoleId(s?.factions[0]?.id ?? '')
                }}
              >
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.year})
                  </option>
                ))}
              </select>
            </div>

            {scenario && (
              <div>
                <label className="label block mb-1">{t('lobby.factionLabel')}</label>
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
                  {scenario.factions.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setRoleId(f.id)}
                      className={
                        'card text-left transition-colors flex items-center gap-2 ' +
                        (roleId === f.id
                          ? 'border-slate-700 bg-slate-50'
                          : 'hover:bg-neutral-100')
                      }
                    >
                      <FactionBadge factionId={f.id} name={f.name} scenarioId={scenarioId} size={28} />
                      <div className="min-w-0">
                        <div
                          className="font-medium truncate"
                          style={{ color: factionTheme(scenarioId, f.id).color }}
                        >
                          {f.name}
                        </div>
                        <div className="text-xs text-neutral-600 truncate">{f.tagline}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {tab === 'create-multi' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label block mb-1">{t('lobby.roomNameLabel')}</label>
                  <input
                    className="input w-full"
                    maxLength={40}
                    placeholder={t('lobby.roomNamePlaceholder')}
                    value={roomName}
                    onChange={(e) => setRoomName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="label block mb-1">{t('lobby.paceLabel')}</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setAsyncMode(false)}
                      className={
                        'card text-left transition-colors ' +
                        (!asyncMode ? 'border-slate-700 bg-slate-50' : 'hover:bg-neutral-100')
                      }
                    >
                      <div className="font-medium">{t('lobby.paceRealtime')}</div>
                      <div className="text-xs text-neutral-600">{t('lobby.paceRealtimeHint')}</div>
                    </button>
                    <button
                      onClick={() => setAsyncMode(true)}
                      className={
                        'card text-left transition-colors ' +
                        (asyncMode ? 'border-slate-700 bg-slate-50' : 'hover:bg-neutral-100')
                      }
                    >
                      <div className="font-medium">{t('lobby.paceAsync')}</div>
                      <div className="text-xs text-neutral-600">{t('lobby.paceAsyncHint')}</div>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {error && <div className="text-sm text-red-700">{error}</div>}

            {tab === 'solo' ? (
              <button className="btn-primary" disabled={loading || !roleId} onClick={createSolo}>
                {loading ? t('lobby.creatingBtn') : t('lobby.createSoloBtn')}
              </button>
            ) : (
              <div className="space-y-1">
                <button className="btn-primary" disabled={loading || !roleId} onClick={createMulti}>
                  {loading ? t('lobby.creatingBtn') : t('lobby.createMultiBtn')}
                </button>
                <p className="text-xs text-neutral-500">{t('lobby.createMultiHint')}</p>
              </div>
            )}
          </div>

          {selectedFaction && (
            <div className="md:w-72 mt-4 md:mt-0 shrink-0">
              <div className="card bg-neutral-50 h-full">
                <div className="flex items-center gap-2 mb-2">
                  <FactionBadge
                    factionId={selectedFaction.id}
                    name={selectedFaction.name}
                    scenarioId={scenarioId}
                    size={40}
                  />
                  <h3 style={{ color: factionTheme(scenarioId, selectedFaction.id).color }}>
                    {selectedFaction.name}
                  </h3>
                </div>
                <div className="text-xs text-neutral-500 mb-2">{selectedFaction.tagline}</div>
                <p className="text-sm text-neutral-700">{selectedFaction.description}</p>
                <div className="mt-3 text-sm grid grid-cols-2 gap-2 font-mono">
                  <div>MIL {selectedFaction.starting_resources.MIL}</div>
                  <div>DIP {selectedFaction.starting_resources.DIP}</div>
                  <div>ECO {selectedFaction.starting_resources.ECO}</div>
                  <div>INT {selectedFaction.starting_resources.INT}</div>
                </div>
                <div className="text-sm text-neutral-600 mt-2">
                  {t('lobby.budgetLabel', { count: selectedFaction.token_budget_per_turn })}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {tab === 'join' && (
        <section className="card space-y-4 max-w-xl">
          <h2>{t('lobby.joinTitle')}</h2>

          <div>
            <label className="label block mb-1">{t('lobby.joinCodeLabel')}</label>
            <input
              className="input w-full font-mono uppercase tracking-widest"
              placeholder="ABCD12"
              maxLength={6}
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            />
          </div>

          {joinLookupLoading && (
            <p className="text-sm text-neutral-500">{t('lobby.joinLookingUp')}</p>
          )}

          {joinLookupError && (
            <p className="text-sm text-red-700">{t('lobby.joinCodeNotFound')}</p>
          )}

          {joinPreview && (
            <div>
              <div className="card bg-neutral-50 text-sm mb-3">
                <div className="font-medium">
                  {joinPreview.room_name || joinPreview.scenario_name}
                </div>
                {joinPreview.room_name && (
                  <div className="text-neutral-600">{joinPreview.scenario_name}</div>
                )}
              </div>
              <label className="label block mb-1">{t('lobby.joinFactionLabel')}</label>
              <div className="grid grid-cols-2 gap-2">
                {joinPreview.slots.map((slot) => (
                  <button
                    key={slot.role_id}
                    disabled={slot.is_taken}
                    onClick={() => setJoinRoleId(slot.role_id)}
                    className={
                      'card text-left transition-colors flex items-center gap-2 ' +
                      (slot.is_taken
                        ? 'opacity-50 cursor-not-allowed'
                        : joinRoleId === slot.role_id
                          ? 'border-slate-700 bg-slate-50'
                          : 'hover:bg-neutral-100')
                    }
                  >
                    <FactionBadge
                      factionId={slot.role_id}
                      name={slot.role_name}
                      scenarioId={joinPreview.scenario_id}
                      size={28}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex justify-between items-baseline gap-2">
                        <div
                          className="font-medium truncate"
                          style={{ color: factionTheme(joinPreview.scenario_id, slot.role_id).color }}
                        >
                          {slot.role_name}
                        </div>
                        {slot.is_taken && (
                          <span className="text-xs text-neutral-500 shrink-0">{t('lobby.slotTaken')}</span>
                        )}
                      </div>
                      <div className="text-xs text-neutral-600 truncate">{slot.tagline}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && <div className="text-sm text-red-700">{error}</div>}

          <button
            className="btn-primary"
            disabled={loading || !joinPreview || !joinRoleId}
            onClick={joinByCode}
          >
            {loading ? t('lobby.joiningBtn') : t('lobby.joinBtn')}
          </button>
        </section>
      )}
      </div>
    </main>
  )
}
