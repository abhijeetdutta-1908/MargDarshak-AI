import { categoryMeta } from '../utils/format'

/** Category-styled cover art used instead of stock photos (no image licensing needed). */
export default function DestinationCover({ destination, className = 'h-44', children, size = 'md' }) {
  const meta = categoryMeta(destination?.category)
  const Icon = meta.icon
  if (destination?.image_url) {
    return (
      <div className={`relative overflow-hidden ${className}`}>
        <img src={destination.image_url} alt={destination.name} loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
        {children}
      </div>
    )
  }
  return (
    <div className={`relative overflow-hidden ${className}`}
      style={{ background: `linear-gradient(135deg, ${meta.from}, ${meta.via} 55%, ${meta.to})` }}>
      <div className="absolute inset-0 opacity-25" style={{ backgroundImage: 'radial-gradient(circle at 20% 20%, white 0 1px, transparent 2px), radial-gradient(circle at 70% 60%, white 0 1px, transparent 2px)', backgroundSize: '28px 28px, 36px 36px' }} />
      <Icon className="absolute -bottom-4 -right-4 text-white/20" size={size === 'lg' ? 220 : 130} strokeWidth={1.2} aria-hidden />
      <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-transparent to-transparent" />
      {children}
    </div>
  )
}
