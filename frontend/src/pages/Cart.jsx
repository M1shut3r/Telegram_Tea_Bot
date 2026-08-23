import WebApp from '@twa-dev/sdk'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import CartItem from '../components/CartItem'
import MaisonHeader from '../components/MaisonHeader'
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
    <main className="px-5 pt-6">
      <MaisonHeader kicker="Ваш выбор" title="Корзина" />
      {loading ? <div className="h-40 animate-pulse bg-paper-deep" /> : null}
      {!loading && items.length === 0 ? (
        <div className="maison-card px-5 py-12 text-center">
          <p className="font-serif text-3xl">Пока пусто</p>
          <p className="mt-3 text-sm font-light text-tg-hint">Добавьте чай из витрины — корзина соберётся сама.</p>
          <button type="button" onClick={() => navigate('/')} className="maison-btn mx-auto mt-7 max-w-[220px]">
            Открыть витрину
          </button>
        </div>
      ) : null}
      <div className="space-y-3">
        {items.map((item) => (
          <CartItem key={item.id} item={item} onChange={handleChange} />
        ))}
      </div>
      {items.length > 0 ? (
        <div className="maison-card mt-8 px-5 py-6">
          <div className="flex items-end justify-between">
            <span className="maison-kicker">Итого</span>
            <span className="font-serif text-4xl">{formatPrice(total)}</span>
          </div>
          <button type="button" onClick={() => navigate('/checkout')} className="maison-btn mt-6">
            Оформить заказ
          </button>
        </div>
      ) : null}
    </main>
  )
}
