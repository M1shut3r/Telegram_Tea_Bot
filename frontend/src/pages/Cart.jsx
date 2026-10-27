import WebApp from '@twa-dev/sdk'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import CartItem from '../components/CartItem'
import { KokoshnikFeast } from '../components/Ornaments'
import PageHeader from '../components/PageHeader'
import { useCart } from '../context/CartContext'
import { formatPacks, formatPrice } from '../utils/format'

export default function Cart() {
  const navigate = useNavigate()
  const { items, total, count, loading, setQuantity } = useCart()
  const [busyId, setBusyId] = useState(null)

  useEffect(() => {
    const openCheckout = () => {
      navigate('/checkout')
    }
    if (count === 0) {
      WebApp.MainButton.hide()
      return undefined
    }
    if (typeof WebApp.MainButton.setParams === 'function') {
      WebApp.MainButton.setParams({ color: '#b8321f', text_color: '#ffffff' })
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
    setBusyId(productId)
    try {
      await setQuantity(productId, Math.max(0, quantity))
      WebApp.HapticFeedback.selectionChanged()
    } catch (requestError) {
      WebApp.showAlert(getErrorMessage(requestError))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <main className="px-4 pt-5">
      <PageHeader kicker="Ваш выбор" title="Корзина" />

      {loading ? <div className="lk-skeleton mt-3 h-40" aria-busy="true" aria-label="Загружаем корзину" /> : null}

      {!loading && items.length === 0 ? (
        <section className="flex flex-col items-center gap-3 pt-3 text-center">
          <KokoshnikFeast className="block h-auto w-full max-w-[378px]" />
          <p className="mt-2 font-display text-[1.75rem]">Пока пусто</p>
          <p className="max-w-[18.75rem] text-[0.95rem] leading-relaxed text-cream-soft">
            Самовар уже кипит — добавьте чай из витрины, и корзина соберётся сама.
          </p>
          <Link to="/" className="lk-btn mt-1.5 w-auto px-7">
            Открыть витрину
          </Link>
        </section>
      ) : null}

      <div className="mt-3 space-y-3">
        {items.map((item) => (
          <CartItem key={item.id} item={item} busy={busyId === item.product_id} onChange={handleChange} />
        ))}
      </div>

      {items.length > 0 ? (
        <section
          aria-label="Итог заказа"
          className="mt-4 flex flex-col gap-3 rounded-[1.25rem] border-[1.5px] border-gold bg-lacquer-panel p-[1.125rem]"
        >
          <div className="flex items-baseline justify-between gap-3">
            <span className="lk-kicker">Итого · {formatPacks(count)}</span>
            <span className="font-display text-[2rem] leading-none text-gold">{formatPrice(total)}</span>
          </div>
          <p className="text-sm leading-relaxed text-cream-soft">
            Доставляем по России. Имя, телефон и адрес — на следующем шаге.
          </p>
          <button type="button" onClick={() => navigate('/checkout')} className="lk-btn">
            Оформить заказ
          </button>
        </section>
      ) : null}
    </main>
  )
}
