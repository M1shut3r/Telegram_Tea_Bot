import axios from 'axios'
import { getTelegramInitData } from '../telegram'

const client = axios.create({
  baseURL: '/api',
})

client.interceptors.request.use((config) => {
  const initData = getTelegramInitData()
  if (initData) {
    config.params = { ...(config.params || {}), _auth: initData }
    config.headers.Authorization = `tma ${initData}`
    config.headers['X-Telegram-Init-Data'] = initData
  }
  const debugId = import.meta.env.VITE_DEBUG_TELEGRAM_ID
  if (debugId) {
    config.headers['X-Debug-Telegram-Id'] = debugId
  }
  return config
})

export function getErrorMessage(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg
  }
  return 'Не удалось выполнить запрос'
}

export async function fetchProducts() {
  const { data } = await client.get('/products')
  return data
}

export async function fetchProduct(productId) {
  const { data } = await client.get(`/products/${productId}`)
  return data
}

export async function fetchCart() {
  const { data } = await client.get('/cart')
  return data
}

export async function addToCart(productId) {
  const { data } = await client.post('/cart/add', { product_id: productId })
  return data
}

export async function setCartQuantity(productId, quantity) {
  const { data } = await client.post('/cart/quantity', {
    product_id: productId,
    quantity,
  })
  return data
}

export async function fetchOrders(status) {
  const { data } = await client.get('/orders/my', {
    params: status ? { status } : {},
  })
  return data
}

export async function fetchAdminOrders(status) {
  const { data } = await client.get('/orders/admin', {
    params: status ? { status } : {},
  })
  return data
}

export async function fetchOrder(orderId) {
  const { data } = await client.get(`/orders/${orderId}`)
  return data
}

export async function cancelOrder(orderId) {
  const { data } = await client.post(`/orders/${orderId}/cancel`)
  return data
}

export async function checkoutOrder(payload) {
  const { data } = await client.post('/orders/checkout', payload)
  return data
}
