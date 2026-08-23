import WebApp from '@twa-dev/sdk'

const STORAGE_KEY = 'tg_init_data'

function readLocationParam(raw, key) {
  const text = raw.startsWith('#') || raw.startsWith('?') ? raw.slice(1) : raw
  return new URLSearchParams(text).get(key) || ''
}

function persistInitData(value) {
  window.__TG_INIT_DATA__ = value
  try {
    sessionStorage.setItem(STORAGE_KEY, value)
  } catch {
    return value
  }
  return value
}

export function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? WebApp
}

export function getTelegramInitData() {
  const sources = [
    window.__TG_INIT_DATA__,
    window.Telegram?.WebApp?.initData,
    WebApp.initData,
    readLocationParam(window.location.hash, 'tgWebAppData'),
    readLocationParam(window.location.search, 'tgWebAppData'),
  ]
  for (const value of sources) {
    if (typeof value === 'string' && value.length > 0) {
      return persistInitData(value)
    }
  }
  try {
    return sessionStorage.getItem(STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

function syncViewportHeight(webApp) {
  const height = webApp.viewportStableHeight || webApp.viewportHeight || window.innerHeight
  if (height) {
    document.documentElement.style.setProperty('--app-height', `${height}px`)
  }
}

function applyFullsize(webApp) {
  if (typeof webApp.ready === 'function') {
    webApp.ready()
  }
  if (webApp.isFullscreen === true && typeof webApp.exitFullscreen === 'function') {
    try {
      webApp.exitFullscreen()
    } catch {
      syncViewportHeight(webApp)
    }
  }
  if (typeof webApp.expand === 'function') {
    webApp.expand()
  }
  if (typeof webApp.disableVerticalSwipes === 'function') {
    webApp.disableVerticalSwipes()
  }
  syncViewportHeight(webApp)
}

export function bootTelegram() {
  const webApp = getTelegramWebApp()
  applyFullsize(webApp)
  if (typeof webApp.setHeaderColor === 'function') {
    webApp.setHeaderColor('#0b0c10')
  }
  if (typeof webApp.setBackgroundColor === 'function') {
    webApp.setBackgroundColor('#0b0c10')
  }
  if (typeof webApp.setBottomBarColor === 'function') {
    webApp.setBottomBarColor('#0b0c10')
  }
  if (typeof webApp.onEvent === 'function') {
    webApp.onEvent('viewportChanged', () => applyFullsize(webApp))
    webApp.onEvent('fullscreenChanged', () => applyFullsize(webApp))
  }
  window.addEventListener('resize', () => syncViewportHeight(webApp))
  ;[80, 250, 700].forEach((delay) => {
    window.setTimeout(() => applyFullsize(webApp), delay)
  })
  getTelegramInitData()
  return webApp
}

export function waitForTelegramInitData(timeoutMs = 2500) {
  return new Promise((resolve) => {
    const existing = getTelegramInitData()
    if (existing) {
      resolve(existing)
      return
    }
    const started = Date.now()
    const timer = window.setInterval(() => {
      const value = getTelegramInitData()
      if (value || Date.now() - started >= timeoutMs) {
        window.clearInterval(timer)
        resolve(value)
      }
    }, 40)
  })
}
