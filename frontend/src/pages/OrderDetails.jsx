import WebApp from '@twa-dev/sdk'
import { useState } from 'react'
import { cancelOrder, getErrorMessage } from '../api/client'
import MaisonHeader from '../components/MaisonHeader'
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
    <main className="px-5 pb-10 pt-6">
      <button type="button" onClick={onBack} className="mb-5 text-[11px] font-medium uppercase tracking-[0.2em] text-tg-hint">
        ← К заказам
      </button>
      <MaisonHeader kicker="Статус" title={`Заказ №${order.id}`}>
        {formatDate(order.created_at)}
      </MaisonHeader>
      {order.status === 'cancelled' ? (
        <section className="maison-card px-5 py-5 text-center text-sm font-medium uppercase tracking-[0.16em] text-tg-hint">
          Заказ отменён
        </section>
      ) : (
        <OrderRoadmap stages={order.roadmap} />
      )}
      {order.tracking_number && (order.status === 'shipped' || order.status === 'done') ? (
        <section className="maison-card mt-3 px-5 py-4 text-center text-[12px] uppercase tracking-[0.16em] text-neon/80">
          Трек-номер {order.tracking_number}
        </section>
      ) : null}
      <section className="maison-card mt-5 px-5 py-5">
        <p className="maison-kicker">Состав</p>
        <ul className="mt-3 space-y-2">
          {order.items.map((item) => (
            <li key={`${item.product_id}-${item.name}`} className="flex items-start justify-between gap-3 text-sm">
              <span className="font-light">
                {item.name} × {item.quantity}
              </span>
              <span className="shrink-0 font-serif text-lg">{formatPrice(item.line_total)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-4 h-px bg-white/10" />
        <p className="mt-4 text-right font-serif text-3xl">{formatPrice(order.total_price)}</p>
      </section>
      <section className="maison-card mt-3 px-5 py-4 text-sm font-light leading-relaxed text-tg-hint">
        <p>{order.customer_name}</p>
        <p>{order.phone}</p>
        <p>
          {order.country}, {order.city}
        </p>
        <p>{order.address}</p>
      </section>
      {canCancel ? (
        <button type="button" disabled={pending} onClick={handleCancel} className="maison-btn-ghost mt-5 text-red-400">
          {pending ? 'Отмена…' : 'Отменить заказ'}
        </button>
      ) : null}
    </main>
  )
}
