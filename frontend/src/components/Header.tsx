import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/authStore'

export function Header() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const refreshToken = useAuthStore((s) => s.refreshToken)
  const clearAuth = useAuthStore((s) => s.clearAuth)

  const lang = i18n.language?.startsWith('en') ? 'en' : 'es'

  const logout = async () => {
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken)
      } catch {
        // local state is cleared regardless of whether the server call succeeds
      }
    }
    clearAuth()
    navigate('/')
  }

  return (
    <header className="border-b border-neutral-200 px-6 py-3 flex items-center justify-between">
      <Link to="/" className="font-medium text-lg">
        {t('common.appName')}
      </Link>
      <div className="flex items-center gap-4 text-sm">
        <div className="flex gap-1">
          <button
            onClick={() => i18n.changeLanguage('es')}
            className={lang === 'es' ? 'font-medium underline' : 'text-neutral-500'}
          >
            ES
          </button>
          <span className="text-neutral-400">/</span>
          <button
            onClick={() => i18n.changeLanguage('en')}
            className={lang === 'en' ? 'font-medium underline' : 'text-neutral-500'}
          >
            EN
          </button>
        </div>
        {user ? (
          <div className="flex items-center gap-3">
            <Link to="/friends" className="text-neutral-600 underline">
              {t('header.friendsLink')}
            </Link>
            <Link to="/profile" className="text-neutral-600 underline">
              @{user.username}
            </Link>
            <button className="underline" onClick={logout}>
              {t('header.logoutBtn')}
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-neutral-500">{t('header.guestLabel')}</span>
            <Link to="/login" className="underline">
              {t('header.loginLink')}
            </Link>
            <Link to="/register" className="underline">
              {t('header.registerLink')}
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
