import type { CSSProperties, ReactNode } from 'react'
import type { Domain, Posture } from '../types/game'

/**
 * Small line-icon set (lucide-derived paths) plus the curated colour palettes
 * used to give postures and resource domains a consistent symbolic identity.
 * Colours are deliberately muted and coordinated — semantic for postures
 * (red/green/amber), a harmonious quartet for domains — to read as "designed"
 * rather than a rainbow.
 */

export const POSTURE_COLOR: Record<Posture, string> = {
  confrontational: '#e06c75', // soft red — escalation
  cooperative: '#98c379', // soft green — accord
  ambiguous: '#e5c07b', // soft amber — concealed intent
}

export const DOMAIN_COLOR: Record<Domain, string> = {
  MIL: '#d08770', // terracotta
  DIP: '#81a1c1', // frost blue
  ECO: '#ebcb8b', // gold
  INT: '#b48ead', // mauve
}

interface SvgProps {
  size?: number
  className?: string
  style?: CSSProperties
  children: ReactNode
}

function Svg({ size = 20, className, style, children }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

type IconProps = Omit<SvgProps, 'children'>

// — Postures ————————————————————————————————————————————————

function SwordsIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5" />
      <line x1="13" x2="19" y1="19" y2="13" />
      <line x1="16" x2="20" y1="16" y2="20" />
      <line x1="19" x2="21" y1="21" y2="19" />
      <polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5" />
      <line x1="5" x2="9" y1="14" y2="18" />
      <line x1="7" x2="4" y1="17" y2="20" />
      <line x1="3" x2="5" y1="19" y2="21" />
    </Svg>
  )
}

export function HandshakeIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="m11 17 2 2a1 1 0 1 0 3-3" />
      <path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4" />
      <path d="m21 3 1 11h-2" />
      <path d="M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3" />
      <path d="M3 4h8" />
    </Svg>
  )
}

// — Panel headers ———————————————————————————————————————————

export function ChatIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z" />
    </Svg>
  )
}

export function LinkIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </Svg>
  )
}

export function UsersIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </Svg>
  )
}

function HalfCircleIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" stroke="none" />
    </Svg>
  )
}

const POSTURE_ICON: Record<Posture, (p: IconProps) => ReactNode> = {
  confrontational: SwordsIcon,
  cooperative: HandshakeIcon,
  ambiguous: HalfCircleIcon,
}

export function PostureIcon({ posture, ...rest }: IconProps & { posture: Posture }) {
  const Cmp = POSTURE_ICON[posture]
  return <Cmp {...rest} />
}

// — Domains —————————————————————————————————————————————————

function ShieldIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    </Svg>
  )
}

function ScaleIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
      <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
      <path d="M7 21h10" />
      <path d="M12 3v18" />
      <path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2" />
    </Svg>
  )
}

function CoinsIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <circle cx="8" cy="8" r="6" />
      <path d="M18.09 10.37A6 6 0 1 1 10.34 18" />
      <path d="M7 6h1v4" />
      <path d="m16.71 13.88.7.71-2.82 2.82" />
    </Svg>
  )
}

export function EyeIcon(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0" />
      <circle cx="12" cy="12" r="3" />
    </Svg>
  )
}

const DOMAIN_ICON: Record<Domain, (p: IconProps) => ReactNode> = {
  MIL: ShieldIcon,
  DIP: ScaleIcon,
  ECO: CoinsIcon,
  INT: EyeIcon,
}

export function DomainIcon({ domain, ...rest }: IconProps & { domain: Domain }) {
  const Cmp = DOMAIN_ICON[domain]
  return <Cmp {...rest} />
}
