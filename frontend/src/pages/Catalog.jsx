import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import WebApp from '@twa-dev/sdk'
import { fetchProducts, getErrorMessage } from '../api/client'
import { getTelegramInitData } from '../telegram'
import { ChevronRightIcon } from '../components/Icons'
import PageHeader from '../components/PageHeader'
import ProductCard from '../components/ProductCard'
import ProductModal from '../components/ProductModal'
import { useCart } from '../context/CartContext'
import { formatPacks, formatPrice, pluralize } from '../utils/format'

export default function Catalog() {
  const navigate = useNavigate()
  const { add, setQuantity, items, count, total } = useCart()
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

  const closeSheet = useCallback(() => setSelected(null), [])

  const goToCart = useCallback(() => {
    setSelected(null)
    navigate('/cart')
  }, [navigate])

  return (
    <main className={['px-4 pt-5', count > 0 ? 'pb-[4.75rem]' : ''].join(' ')}>
      <PageHeader variant="emblem" />

      <div className="mb-4 mt-5 flex items-baseline justify-between">
        <h1 className="font-display text-[1.875rem] leading-tight">Витрина</h1>
        {products.length > 0 ? (
          <span className="text-sm text-cream-soft">
            {products.length} {pluralize(products.length, ['сорт', 'сорта', 'сортов'])}
          </span>
        ) : null}
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-3" aria-busy="true" aria-label="Загружаем витрину">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="lk-skeleton h-80" />
          ))}
        </div>
      ) : null}

      {error ? <p className="lk-card px-4 py-5 text-center text-sm text-cream-soft">{error}</p> : null}

      {!loading && !error && products.length === 0 ? (
        <p className="lk-card px-4 py-10 text-center text-sm text-cream-soft">Каталог пока пуст. Загляните позже.</p>
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
        onClose={closeSheet}
        onGoToCart={goToCart}
        onIncrement={handleIncrement}
        onDecrement={handleDecrement}
      />

      {count > 0 ? (
        <div className="lk-cart-bar">
          <Link
            to="/cart"
            className="flex min-h-[3.25rem] items-center justify-between rounded-[0.875rem] bg-gold px-4 text-[0.95rem] font-extrabold text-lacquer no-underline"
          >
            <span>
              {formatPacks(count)} · {formatPrice(total)}
            </span>
            <span className="flex items-center gap-1">
              Корзина
              <ChevronRightIcon />
            </span>
          </Link>
        </div>
      ) : null}
    </main>
  )
}
