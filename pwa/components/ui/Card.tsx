import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
  hover?: boolean
  glassMorphism?: 'subtle' | 'medium' | 'heavy'
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  hover = true,
  glassMorphism = 'subtle'
}) => {
  const baseClasses = `glass-${glassMorphism} rounded-2xl transition-all duration-300`
  const hoverClasses = hover ? 'hover:transform hover:translate-y-[-2px] hover:shadow-xl' : ''
  const clickableClasses = onClick ? 'cursor-pointer' : ''

  return (
    <div
      className={`${baseClasses} ${hoverClasses} ${clickableClasses} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue
}) => {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-gray-400'
  }

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→'
  }

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm text-white/50 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-white">{value}</h3>
          {subtitle && <p className="text-sm text-white/70 mt-1">{subtitle}</p>}
        </div>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      {trend && trendValue && (
        <div className={`flex items-center space-x-1 text-sm ${trendColors[trend]}`}>
          <span>{trendIcons[trend]}</span>
          <span>{trendValue}</span>
        </div>
      )}
    </Card>
  )
}

interface ListItemProps {
  title: string
  subtitle?: string
  icon?: string
  rightElement?: React.ReactNode
  onClick?: () => void
}

export const ListItem: React.FC<ListItemProps> = ({
  title,
  subtitle,
  icon,
  rightElement,
  onClick
}) => {
  return (
    <div
      className="flex items-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
      onClick={onClick}
    >
      {icon && <span className="text-xl mr-3">{icon}</span>}
      <div className="flex-1">
        <p className="font-medium">{title}</p>
        {subtitle && <p className="text-sm text-white/50">{subtitle}</p>}
      </div>
      {rightElement}
    </div>
  )
}
