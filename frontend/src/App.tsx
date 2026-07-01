import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { Briefing } from './pages/Briefing'
import { Friends } from './pages/Friends'
import { GameRoom } from './pages/GameRoom'
import { Lobby } from './pages/Lobby'
import { Login } from './pages/Login'
import { Profile } from './pages/Profile'
import { Register } from './pages/Register'
import { Resolution } from './pages/Resolution'
import { WaitingRoom } from './pages/WaitingRoom'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Header />
        {/* flex-1 so pages that opt in (e.g. Lobby) can vertically center
            their content in the remaining viewport height instead of
            leaving a dead gap below on large screens. Pages that don't
            opt in render at their natural height, unaffected. */}
        <div className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Lobby />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/friends" element={<Friends />} />
            <Route path="/games/:gameId/waiting" element={<WaitingRoom />} />
            <Route path="/games/:gameId/briefing" element={<Briefing />} />
            <Route path="/games/:gameId/game" element={<GameRoom />} />
            <Route path="/games/:gameId/resolution" element={<Resolution />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
