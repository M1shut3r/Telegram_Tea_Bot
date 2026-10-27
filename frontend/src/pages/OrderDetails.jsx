import WebApp from '@twa-dev/sdk'
import { useState } from 'react'
import { cancelOrder, getErrorMessage } from '../api/client'
import { CancelledIcon, ChevronLeftIcon } from '../components/Icons'
import OrderRoadmap from '../components/OrderRoadmap'
import PageHeader from '../components/PageHeader'
import { formatDate, formatPrice } from '../utils/format'
import { hasTracking } from '../utils/orderStatus'

const CANCELLABLE_STATUSES = new Set(['new', 'in_progress', 'packed'])

function LineThumb({ productId }) {
  const [hidden, setHidden] = useState(false)
  if (hidden) {
    return null
  }
  return (
    <img
      src={`/api/products/${productId}/photo`}
      alt=""
      loading="lazy"
      onError={() => setHidden(true)}
      className="h-[3.25rem] w-10 flex-none rounded-md border-[1.5px] border-gold object-cover"
    />
  )
}

async function copyText(value) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value)
      return true
    }
  } catch {
    // fall through to the legacy path
  }
  try {
    const field = document.createElement('textarea')
    field.value = value
    field.setAttribute('readonly', '')
    field.style.position = 'fixed'
    field.style.opacity = '0'
    document.body.appendChild(field)
    field.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(field)
    return ok
  } catch {
    return false
  }
}

export default function OrderDetails({ order, onBack, onCancelled }) {
  const [pending, setPending] = useState(false)
  const [copied, setCopied] = useState(false)
  const canCancel = order.can_cancel === true || CANCELLABLE_STATUSES.has(order.status)
  const cancelled = order.status === 'cancelled'

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

  const handleCopy = async () => {
    const ok = await copyText(order.tracking_number)
    if (ok) {
      setCopied(true)
      WebApp.HapticFeedback.notificationOccurred('success')
    }
  }

  return (
    <main className="px-4 pb-10 pt-3">
      <button
        type="button"
        onClick={onBack}
        className="-ml-2 mb-1 flex min-h-11 items-center gap-1 px-2 text-[0.95rem] font-extrabold text-gold"
      >
        <ChevronLeftIcon />
        К заказам
      </button>

      <PageHeader kicker={`Статус · ${order.status_title}`} title={`Заказ №${order.id}`} emblem={false}>
        {formatDate(order.created_at)}
      </PageHeader>

      <div className="mt-3 flex flex-col gap-3.5">
        {cancelled ? (
          <section
            role="status"
            className="flex items-center justify-center gap-2.5 rounded-2xl border border-lacquer-line bg-lacquer-raised px-4 py-[1.125rem] text-[0.95rem] font-extrabold uppercase tracking-[0.08em] text-cream-muted"
          >
            <CancelledIcon />
            Заказ отменён
          </section>
        ) : (
          <OrderRoadmap stages={order.roadmap} />
        )}

        {hasTracking(order) ? (
          <section className="flex items-center justify-between gap-2.5 rounded-2xl border-[1.5px] border-gold bg-lacquer-panel py-3 pl-4 pr-3">
            <span className="flex min-w-0 flex-col gap-0.5">
              <span className="lk-kicker">Трек-номер</span>
              <span className="break-all text-[1.0625rem] font-extrabold tracking-[0.04em]">{order.tracking_number}</span>
            </span>
            <button type="button" onClick={handleCopy} className="lk-btn-ghost min-h-11 w-auto flex-none rounded-xl px-3.5 text-sm">
              {copied ? 'Скопировано' : 'Скопировать'}
            </button>
          </section>
        ) : null}

        <section aria-labelledby="order-items" className="lk-card flex flex-col gap-2.5 px-4 py-3.5">
          <h2 id="order-items" className="lk-kicker text-gold">
            Состав
          </h2>
          <ul className="flex flex-col gap-2.5">
            {order.items.map((item) => (
              <li key={`${item.product_id}-${item.name}`} className="flex items-center gap-3">
                <LineThumb productId={item.product_id} />
                <span className="flex-1 text-[0.95rem]">
                  {item.name} × {item.quantity}
                </span>
                <span className="flex-none text-[0.95rem] font-extrabold">{formatPrice(item.line_total)}</span>
              </li>
            ))}
          </ul>
          <div className="h-px bg-lacquer-line" />
          <div className="flex items-baseline justify-between">
            <span className="lk-kicker">Итого</span>
            <span className="font-display text-[1.75rem] text-gold">{formatPrice(order.total_price)}</span>
          </div>
        </section>

        <section aria-labelledby="order-recipient" className="lk-card flex flex-col gap-1 px-4 py-3.5 text-[0.95rem] leading-snug">
          <h2 id="order-recipient" className="lk-kicker mb-1 text-gold">
            Получатель
          </h2>
          <span>{order.customer_name}</span>
          <span>{order.phone}</span>
          <span className="text-cream-soft">
            {order.country}, {order.city}, {order.address}
          </span>
        </section>

        {canCancel && !cancelled ? (
          <button type="button" disabled={pending} onClick={handleCancel} className="lk-btn-danger">
            {pending ? 'Отменяем…' : 'Отменить заказ'}
          </button>
        ) : null}
      </div>
    </main>
  )
}
