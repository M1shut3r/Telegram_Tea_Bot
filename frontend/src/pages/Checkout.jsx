import WebApp from '@twa-dev/sdk'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { checkoutOrder, getErrorMessage } from '../api/client'
import MaisonHeader from '../components/MaisonHeader'
import { useCart } from '../context/CartContext'
import { formatPrice } from '../utils/format'

const PHONE_PATTERN = /^\+?[0-9][0-9\-\s()]{8,20}$/

const emptyForm = {
  customer_name: '',
  phone: '',
  country: 'Россия',
  city: '',
  address: '',
}

export default function Checkout() {
  const navigate = useNavigate()
  const { items, total, count, refresh } = useCart()
  const [form, setForm] = useState(emptyForm)
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const goBack = () => {
      navigate('/cart')
    }
    WebApp.BackButton.show()
    WebApp.BackButton.onClick(goBack)
    WebApp.MainButton.hide()
    return () => {
      WebApp.BackButton.offClick(goBack)
      WebApp.BackButton.hide()
    }
  }, [navigate])

  const updateField = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setErrors((current) => ({ ...current, [field]: '' }))
  }

  const validate = () => {
    const next = {}
    if (form.customer_name.trim().length < 2) {
      next.customer_name = 'Введите имя'
    }
    if (!PHONE_PATTERN.test(form.phone.trim())) {
      next.phone = 'Введите телефон в формате +79991234567'
    }
    if (form.country !== 'Россия') {
      next.country = 'Доставка только по России'
    }
    if (form.city.trim().length < 2) {
      next.city = 'Введите город'
    }
    if (form.address.trim().length < 5) {
      next.address = 'Введите улицу, дом и квартиру'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!validate() || submitting) {
      return
    }
    setSubmitting(true)
    try {
      const result = await checkoutOrder({
        customer_name: form.customer_name.trim(),
        phone: form.phone.trim(),
        country: 'Россия',
        city: form.city.trim(),
        address: form.address.trim(),
      })
      await refresh()
      WebApp.HapticFeedback.notificationOccurred('success')
      WebApp.showAlert(`Заказ №${result.order.id} принят!`)
      navigate('/orders')
    } catch (requestError) {
      WebApp.showAlert(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  if (count === 0) {
    return (
      <main className="px-5 pt-6">
        <MaisonHeader kicker="Доставка" title="Оформление" />
        <p className="text-center text-sm font-light text-tg-hint">Корзина пуста. Добавьте чай, чтобы оформить заказ.</p>
        <button type="button" onClick={() => navigate('/')} className="maison-btn mx-auto mt-6 max-w-[220px]">
          К витрине
        </button>
      </main>
    )
  }

  return (
    <main className="px-5 pb-10 pt-6">
      <MaisonHeader kicker="Доставка" title="Оформление">
        Итого {formatPrice(total)} · {items.length} поз.
      </MaisonHeader>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="maison-kicker mb-2 block">Имя</span>
          <input
            value={form.customer_name}
            onChange={updateField('customer_name')}
            className="maison-field h-12 px-4"
            autoComplete="name"
          />
          {errors.customer_name ? <span className="mt-1 block text-xs text-red-400">{errors.customer_name}</span> : null}
        </label>
        <label className="block">
          <span className="maison-kicker mb-2 block">Телефон</span>
          <input
            value={form.phone}
            onChange={updateField('phone')}
            className="maison-field h-12 px-4"
            inputMode="tel"
            autoComplete="tel"
            placeholder="+79991234567"
          />
          {errors.phone ? <span className="mt-1 block text-xs text-red-400">{errors.phone}</span> : null}
        </label>
        <label className="block">
          <span className="maison-kicker mb-2 block">Страна</span>
          <select value={form.country} onChange={updateField('country')} className="maison-field h-12 appearance-none px-4">
            <option value="Россия">Россия</option>
            <option value="other" disabled>
              Другие страны недоступны
            </option>
          </select>
          {errors.country ? <span className="mt-1 block text-xs text-red-400">{errors.country}</span> : null}
        </label>
        <label className="block">
          <span className="maison-kicker mb-2 block">Город</span>
          <input
            value={form.city}
            onChange={updateField('city')}
            className="maison-field h-12 px-4"
            autoComplete="address-level2"
          />
          {errors.city ? <span className="mt-1 block text-xs text-red-400">{errors.city}</span> : null}
        </label>
        <label className="block">
          <span className="maison-kicker mb-2 block">Адрес</span>
          <textarea
            value={form.address}
            onChange={updateField('address')}
            className="maison-field min-h-[96px] resize-none px-4 py-3"
            autoComplete="street-address"
            placeholder="Улица, дом, квартира"
          />
          {errors.address ? <span className="mt-1 block text-xs text-red-400">{errors.address}</span> : null}
        </label>
        <button type="submit" disabled={submitting} className="maison-btn">
          {submitting ? 'Отправляем…' : 'Подтвердить заказ'}
        </button>
      </form>
    </main>
  )
}
