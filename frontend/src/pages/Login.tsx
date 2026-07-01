import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/authStore'

export function Login() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await authApi.login(email, password)
      setAuth({ access_token: res.access_token, refresh_token: res.refresh_token }, res.user)
      i18n.changeLanguage(res.user.locale)
      navigate('/')
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-sm mx-auto p-8 space-y-6">
      <h1>{t('auth.loginTitle')}</h1>
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
          <label className="label block mb-1">{t('auth.passwordLabel')}</label>
          <input
            type="password"
            required
            className="input w-full"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button className="btn-primary w-full" disabled={loading} type="submit">
          {loading ? t('auth.loggingInBtn') : t('auth.loginBtn')}
        </button>
      </form>
      <p className="text-sm text-neutral-600 text-center">
        {t('auth.noAccount')}{' '}
        <Link to="/register" className="underline">
          {t('auth.registerLink')}
        </Link>
      </p>
    </main>
  )
}
