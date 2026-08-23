import WebApp from '@twa-dev/sdk'
import { useEffect, useState } from 'react'
import { fetchOrder, fetchOrders, getErrorMessage } from '../api/client'
import MaisonHeader from '../components/MaisonHeader'
import OrderDetails from './OrderDetails'
import { formatDate, formatPrice } from '../utils/format'

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
    <main className="px-5 pt-6">
      <MaisonHeader kicker="История" title="Заказы" />
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-28 animate-pulse bg-paper-deep" />
          ))}
        </div>
      ) : null}
      {error ? <p className="maison-card px-4 py-5 text-center text-sm text-tg-hint">{error}</p> : null}
      {!loading && !error && orders.length === 0 ? (
        <p className="maison-card px-5 py-12 text-center text-sm font-light text-tg-hint">
          Заказов пока нет. Первый чай — всегда особенный.
        </p>
      ) : null}
      <div className="space-y-3">
        {orders.map((order) => (
          <button
            key={order.id}
            type="button"
            onClick={() => {
              if (!detailLoading) {
                openOrder(order.id)
              }
            }}
            className="maison-card w-full px-5 py-5 text-left"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-serif text-2xl">Заказ №{order.id}</p>
                <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-tg-hint">{formatDate(order.created_at)}</p>
              </div>
              <span className="border border-white/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-tg-hint">
                {order.status_title}
              </span>
            </div>
            <p className="mt-4 text-sm font-light text-tg-hint">
              {order.city}, {order.address}
            </p>
            <p className="mt-3 font-serif text-xl">{formatPrice(order.total_price)}</p>
            {order.tracking_number && (order.status === 'shipped' || order.status === 'done') ? (
              <p className="mt-3 text-[11px] uppercase tracking-[0.14em] text-neon/80">Трек {order.tracking_number}</p>
            ) : null}
          </button>
        ))}
      </div>
    </main>
  )
}
