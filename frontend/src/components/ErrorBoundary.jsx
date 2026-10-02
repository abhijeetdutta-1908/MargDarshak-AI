import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('UI error', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <main className="flex min-h-[60vh] flex-col items-center justify-center gap-3 px-4 text-center">
        <h1 className="text-2xl font-bold">Something went wrong on this page</h1>
        <p className="max-w-md text-slate-600">The error has been logged. You can reload the page or go back home.</p>
        <div className="flex gap-2">
          <button className="rounded-xl bg-brand-600 px-4 py-2 font-semibold text-white" onClick={() => window.location.reload()}>Reload</button>
          <a className="rounded-xl border border-slate-300 px-4 py-2 font-semibold" href="/">Home</a>
        </div>
      </main>
    )
  }
}
