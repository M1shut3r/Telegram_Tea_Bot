import WebApp from '@twa-dev/sdk'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import CartItem from '../components/CartItem'
import { useCart } from '../context/CartContext'
import { formatPrice } from '../utils/format'

export default function Cart() {
  const navigate = useNavigate()
  const { items, total, count, loading, setQuantity } = useCart()

  useEffect(() => {
    const openCheckout = () => {
      navigate('/checkout')
    }
    if (count === 0) {
      WebApp.MainButton.hide()
      return undefined
    }
    WebApp.MainButton.setText('Оформить заказ')
    WebApp.MainButton.show()
    WebApp.MainButton.onClick(openCheckout)
    return () => {
      WebApp.MainButton.offClick(openCheckout)
      WebApp.MainButton.hide()
    }
  }, [count, navigate])

  const handleChange = async (productId, quantity) => {
    try {
      await setQuantity(productId, quantity)
      WebApp.HapticFeedback.selectionChanged()
    } catch (requestError) {
      WebApp.showAlert(getErrorMessage(requestError))
    }
  }

  return (
    <main className="px-5 pt-8">
      <header className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tg-hint">Ваш выбор</p>
        <h1 className="mt-2 font-serif text-[34px] leading-none">Корзина</h1>
      </header>
      {loading ? <div className="h-40 animate-pulse rounded-[28px] bg-tg-secondary" /> : null}
      {!loading && items.length === 0 ? (
        <div className="rounded-[28px] bg-tg-secondary px-5 py-10 text-center">
          <p className="font-serif text-2xl">Пока пусто</p>
          <p className="mt-2 text-sm text-tg-hint">Добавьте чай из витрины — корзина соберётся сама.</p>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="mt-6 h-12 rounded-2xl bg-tg-button px-6 text-sm font-semibold text-tg-button-text"
          >
            Открыть каталог
          </button>
        </div>
      ) : null}
      <div className="space-y-3">
        {items.map((item) => (
          <CartItem key={item.id} item={item} onChange={handleChange} />
        ))}
      </div>
      {items.length > 0 ? (
        <div className="mt-8 rounded-[28px] bg-tg-secondary px-5 py-5">
          <div className="flex items-end justify-between">
            <span className="text-sm text-tg-hint">Итого</span>
            <span className="font-serif text-3xl">{formatPrice(total)}</span>
          </div>
          <button
            type="button"
            onClick={() => navigate('/checkout')}
            className="mt-5 flex h-14 w-full items-center justify-center rounded-2xl bg-tg-button text-base font-semibold text-tg-button-text"
          >
            Оформить заказ
          </button>
        </div>
      ) : null}
    </main>
  )
}
