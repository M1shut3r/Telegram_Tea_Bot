import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { addToCart, fetchCart, setCartQuantity } from '../api/client'
import { waitForTelegramInitData } from '../telegram'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState('0.00')
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)

  const applyCart = useCallback((data) => {
    setItems(data.items ?? [])
    setTotal(data.total ?? '0.00')
    setCount(data.count ?? 0)
  }, [])

  const refresh = useCallback(async () => {
    try {
      const data = await fetchCart()
      applyCart(data)
      return data
    } finally {
      setLoading(false)
    }
  }, [applyCart])

  useEffect(() => {
    let cancelled = false
    waitForTelegramInitData(8000)
      .then(() => {
        if (cancelled) {
          return
        }
        return refresh()
      })
      .catch(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const add = useCallback(
    async (productId) => {
      const data = await addToCart(productId)
      applyCart(data)
      return data
    },
    [applyCart],
  )

  const setQuantity = useCallback(
    async (productId, quantity) => {
      const data = await setCartQuantity(productId, quantity)
      applyCart(data)
      return data
    },
    [applyCart],
  )

  const value = useMemo(
    () => ({ items, total, count, loading, refresh, add, setQuantity }),
    [items, total, count, loading, refresh, add, setQuantity],
  )

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const context = useContext(CartContext)
  if (context == null) {
    throw new Error('CartProvider is required')
  }
  return context
}
