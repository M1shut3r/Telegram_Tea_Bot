import WebApp from '@twa-dev/sdk'
import { useState } from 'react'
import { cancelOrder, getErrorMessage } from '../api/client'
import OrderRoadmap from '../components/OrderRoadmap'
import { formatDate, formatPrice } from '../utils/format'

const CANCELLABLE_STATUSES = new Set(['new', 'in_progress', 'packed'])

export default function OrderDetails({ order, onBack, onCancelled }) {
  const [pending, setPending] = useState(false)
  const canCancel = order.can_cancel === true || CANCELLABLE_STATUSES.has(order.status)

  const handleCancel = () => {
    if (pending) {
      return
    }
    const run = async (confirmed) => {
      if (!confirmed) {
        return
      }
      setPending(true)
      try {
        const detail = await cancelOrder(order.id)
        onCancelled(detail)
        WebApp.HapticFeedback.notificationOccurred('success')
      } catch (requestError) {
        WebApp.showAlert(getErrorMessage(requestError))
      } finally {
        setPending(false)
      }
    }
    if (typeof WebApp.showConfirm === 'function') {
      WebApp.showConfirm(`Отменить заказ №${order.id}?`, run)
      return
    }
    run(true)
  }

  return (
    <main className="px-5 pb-10 pt-8">
      <button type="button" onClick={onBack} className="mb-6 text-sm font-semibold text-tg-button">
        ← К заказам
      </button>
      <header className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tg-hint">Статус</p>
        <h1 className="mt-2 font-serif text-[34px] leading-none">Заказ №{order.id}</h1>
        <p className="mt-2 text-sm text-tg-hint">{formatDate(order.created_at)}</p>
      </header>
      {order.status === 'cancelled' ? (
        <section className="rounded-[28px] bg-tg-secondary px-5 py-4 text-sm font-semibold">❌ Заказ отменён</section>
      ) : (
        <OrderRoadmap stages={order.roadmap} />
      )}
      {order.tracking_number && (order.status === 'shipped' || order.status === 'done') ? (
        <section className="mt-4 rounded-[28px] bg-tg-secondary px-5 py-4 text-sm font-semibold">
          📮 Трек-номер: {order.tracking_number}
        </section>
      ) : null}
      <section className="mt-8 rounded-[28px] bg-tg-secondary px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-tg-hint">Состав</p>
        <ul className="mt-3 space-y-2">
          {order.items.map((item) => (
            <li key={`${item.product_id}-${item.name}`} className="flex items-start justify-between gap-3 text-sm">
              <span>
                {item.name} × {item.quantity}
              </span>
              <span className="shrink-0 font-semibold">{formatPrice(item.line_total)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 font-serif text-2xl">{formatPrice(order.total_price)}</p>
      </section>
      <section className="mt-3 rounded-[28px] bg-tg-secondary px-5 py-4 text-sm leading-relaxed text-tg-hint">
        <p>{order.customer_name}</p>
        <p>{order.phone}</p>
        <p>
          {order.country}, {order.city}
        </p>
        <p>{order.address}</p>
      </section>
      {canCancel ? (
        <button
          type="button"
          disabled={pending}
          onClick={handleCancel}
          className="mt-5 flex h-14 w-full items-center justify-center rounded-2xl bg-tg-secondary text-base font-semibold text-red-500 disabled:opacity-60"
        >
          {pending ? 'Отмена…' : '❌ Отменить заказ'}
        </button>
      ) : null}
    </main>
  )
}
