import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/authStore'

export function Register() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const locale = i18n.language?.startsWith('en') ? 'en' : 'es'
      const res = await authApi.register(email, username, password, locale)
      setAuth({ access_token: res.access_token, refresh_token: res.refresh_token }, res.user)
      navigate('/')
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-sm mx-auto p-8 space-y-6">
      <h1>{t('auth.registerTitle')}</h1>
      <form className="card space-y-4" onSubmit={submit}>
        <div>
          <label className="label block mb-1">{t('auth.emailLabel')}</label>
          <input
            type="email"
            required
            className="input w-full"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="label block mb-1">{t('auth.usernameLabel')}</label>
          <input
            required
            minLength={3}
            maxLength={24}
            pattern="[a-zA-Z0-9_]+"
            className="input w-full"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="label block mb-1">{t('auth.passwordLabel')}</label>
          <input
            type="password"
            required
            minLength={8}
            className="input w-full"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button className="btn-primary w-full" disabled={loading} type="submit">
          {loading ? t('auth.registeringBtn') : t('auth.registerBtn')}
        </button>
      </form>
      <p className="text-sm text-neutral-600 text-center">
        {t('auth.haveAccount')}{' '}
        <Link to="/login" className="underline">
          {t('auth.loginLink')}
        </Link>
      </p>
    </main>
  )
}
