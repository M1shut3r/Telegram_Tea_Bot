import { useEffect, useState } from 'react'
import { fetchProducts, getErrorMessage } from '../api/client'
import { getTelegramInitData } from '../telegram'
import MaisonHeader from '../components/MaisonHeader'
import ProductCard from '../components/ProductCard'
import ProductModal from '../components/ProductModal'
import { useCart } from '../context/CartContext'
import WebApp from '@twa-dev/sdk'

export default function Catalog() {
  const { add, setQuantity, items } = useCart()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [pendingId, setPendingId] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchProducts()
      .then((data) => {
        if (!cancelled) {
          setProducts(data)
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(getErrorMessage(requestError))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const quantityOf = (productId) => items.find((item) => item.product_id === productId)?.quantity ?? 0

  const handleIncrement = async (product) => {
    if (!getTelegramInitData()) {
      WebApp.showAlert('Корзина доступна только из Telegram. Нажмите «Витрина» в меню бота.')
      return
    }
    setPendingId(product.id)
    try {
      await add(product.id)
      WebApp.HapticFeedback.impactOccurred('light')
    } catch (requestError) {
      WebApp.showAlert(getErrorMessage(requestError))
    } finally {
      setPendingId(null)
    }
  }

  const handleDecrement = async (product) => {
    const next = quantityOf(product.id) - 1
    setPendingId(product.id)
    try {
      await setQuantity(product.id, Math.max(0, next))
      WebApp.HapticFeedback.selectionChanged()
    } catch (requestError) {
      WebApp.showAlert(getErrorMessage(requestError))
    } finally {
      setPendingId(null)
    }
  }

  return (
    <main className="px-5 pt-6">
      <MaisonHeader kicker="Чайная" title="Витрина">
        Ночная витрина. Выбирайте спокойно.
      </MaisonHeader>
      {loading ? (
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-80 animate-pulse bg-paper-deep" />
          ))}
        </div>
      ) : null}
      {error ? <p className="maison-card px-4 py-5 text-center text-sm text-tg-hint">{error}</p> : null}
      {!loading && !error && products.length === 0 ? (
        <p className="maison-card px-4 py-10 text-center text-sm font-light text-tg-hint">
          Каталог пока пуст. Загляните позже.
        </p>
      ) : null}
      <div className="grid grid-cols-2 gap-3">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            quantity={quantityOf(product.id)}
            busy={pendingId === product.id}
            onOpen={setSelected}
            onIncrement={handleIncrement}
            onDecrement={handleDecrement}
          />
        ))}
      </div>
      <ProductModal
        product={selected}
        quantity={selected ? quantityOf(selected.id) : 0}
        busy={selected != null && pendingId === selected.id}
        onClose={() => setSelected(null)}
        onIncrement={handleIncrement}
        onDecrement={handleDecrement}
      />
    </main>
  )
}
