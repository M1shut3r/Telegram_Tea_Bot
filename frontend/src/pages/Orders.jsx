import WebApp from '@twa-dev/sdk'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchOrder, fetchOrders, getErrorMessage } from '../api/client'
import { ChevronRightIcon, ParcelIcon } from '../components/Icons'
import PageHeader from '../components/PageHeader'
import OrderDetails from './OrderDetails'
import { formatDate, formatPrice } from '../utils/format'
import { PROGRESS_STEPS, STATUS_RANK, hasTracking, statusPillClass } from '../utils/orderStatus'

function OrderCard({ order, onOpen, disabled }) {
  const cancelled = order.status === 'cancelled'
  const rank = STATUS_RANK[order.status] ?? 0

  return (
    <button
      type="button"
      onClick={() => onOpen(order.id)}
      disabled={disabled}
      className={[
        'flex w-full flex-col gap-2.5 rounded-2xl border px-4 py-3.5 text-left',
        cancelled ? 'border-lacquer-line bg-[#1a130f] text-cream-muted' : 'border-gold-muted bg-lacquer-panel text-cream',
      ].join(' ')}
    >
      <span className="flex items-start justify-between gap-2.5">
        <span className="flex flex-col gap-0.5">
          <span className="font-display text-[1.375rem] leading-tight">Заказ №{order.id}</span>
          <span className={['text-[0.8125rem]', cancelled ? 'text-cream-dim' : 'text-cream-soft'].join(' ')}>
            {formatDate(order.created_at)}
          </span>
        </span>
        <span className={['flex-none rounded-full px-2.5 py-1 text-xs font-extrabold', statusPillClass(order.status)].join(' ')}>
          {order.status_title}
        </span>
      </span>

      {cancelled ? null : (
        <span aria-hidden="true" className="grid grid-cols-4 gap-1">
          {Array.from({ length: PROGRESS_STEPS }).map((_, index) => (
            <span key={index} className={['h-1 rounded-sm', rank >= index + 1 ? 'bg-gold' : 'bg-lacquer-line'].join(' ')} />
          ))}
        </span>
      )}

      {cancelled ? null : (
        <span className="text-sm text-cream-soft">
          {order.city}, {order.address}
        </span>
      )}

      {hasTracking(order) ? (
        <span className="flex items-center gap-1.5 text-[0.8125rem] font-bold">
          <ParcelIcon className="text-gold" />
          Трек {order.tracking_number}
        </span>
      ) : null}

      <span className="flex items-center justify-between">
        <span className={['font-display text-[1.375rem]', cancelled ? '' : 'text-gold'].join(' ')}>
          {formatPrice(order.total_price)}
        </span>
        <span className="flex items-center gap-0.5 text-sm font-extrabold text-gold">
          Подробнее
          <ChevronRightIcon size={16} />
        </span>
      </span>
    </button>
  )
}

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchOrders()
      .then((data) => {
        if (!cancelled) {
          setOrders(data)
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

  useEffect(() => {
    if (selected == null) {
      WebApp.BackButton.hide()
      return undefined
    }
    const goBack = () => {
      setSelected(null)
    }
    WebApp.BackButton.show()
    WebApp.BackButton.onClick(goBack)
    return () => {
      WebApp.BackButton.offClick(goBack)
      WebApp.BackButton.hide()
    }
  }, [selected])

  const openOrder = async (orderId) => {
    if (detailLoading) {
      return
    }
    setDetailLoading(true)
    try {
      const detail = await fetchOrder(orderId)
      setSelected(detail)
    } catch (requestError) {
      WebApp.showAlert(getErrorMessage(requestError))
    } finally {
      setDetailLoading(false)
    }
  }

  const handleCancelled = (detail) => {
    setSelected(detail)
    setOrders((current) => current.map((item) => (item.id === detail.id ? { ...item, ...detail } : item)))
  }

  if (selected != null) {
    return <OrderDetails order={selected} onBack={() => setSelected(null)} onCancelled={handleCancelled} />
  }

  return (
    <main className="px-4 pt-5">
      <PageHeader kicker="История" title="Заказы" />

      {loading ? (
        <div className="mt-3 space-y-3" aria-busy="true" aria-label="Загружаем заказы">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="lk-skeleton h-36" />
          ))}
        </div>
      ) : null}

      {error ? <p className="lk-card mt-3 px-4 py-5 text-center text-sm text-cream-soft">{error}</p> : null}

      {!loading && !error && orders.length === 0 ? (
        <section className="lk-card mt-3 flex flex-col items-center gap-3 px-5 py-10 text-center">
          <p className="font-display text-2xl">Заказов пока нет</p>
          <p className="text-sm text-cream-soft">Первый чай — всегда особенный.</p>
          <Link to="/" className="lk-btn mt-2 w-auto px-7">
            Открыть витрину
          </Link>
        </section>
      ) : null}

      <div className="mt-3 space-y-3">
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} onOpen={openOrder} disabled={detailLoading} />
        ))}
      </div>
    </main>
  )
}
