import { createContext, useContext, useEffect, useState } from 'react'
import { getConfig } from '../services/api'

const DEFAULT = { maps: { provider: 'openstreetmap', browser_key: null }, live_weather: false, live_places: false }
const ConfigContext = createContext(DEFAULT)

export function ConfigProvider({ children }) {
  const [config, setConfig] = useState(DEFAULT)
  useEffect(() => { getConfig().then(setConfig).catch(() => {}) }, [])
  return <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>
}

export const useConfig = () => useContext(ConfigContext)
