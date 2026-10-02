export default function Spinner({ full = false, className = '' }) {
  const ring = <span className={`inline-block h-5 w-5 animate-spin rounded-full border-2 border-current border-r-transparent ${className}`} role="status" aria-label="Loading" />
  return full ? <div className="flex min-h-[60vh] items-center justify-center text-brand-600">{ring}</div> : ring
}
