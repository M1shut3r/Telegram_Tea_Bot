import WebApp from '@twa-dev/sdk'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { checkoutOrder, getErrorMessage } from '../api/client'
import { ChevronDownIcon, ChevronLeftIcon } from '../components/Icons'
import PageHeader from '../components/PageHeader'
import { useCart } from '../context/CartContext'
import { formatPacks, formatPrice } from '../utils/format'

const PHONE_PATTERN = /^\+?[0-9][0-9\-\s()]{8,20}$/

const emptyForm = {
  customer_name: '',
  phone: '',
  country: 'Россия',
  city: '',
  address: '',
}

function Field({ id, label, error, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[0.8125rem] font-extrabold uppercase tracking-[0.12em] text-cream-soft">
        {label}
      </label>
      {children}
      {error ? (
        <span id={`${id}-error`} className="text-[0.8125rem] text-danger">
          {error}
        </span>
      ) : null}
    </div>
  )
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
    const firstInvalid = Object.keys(next)[0]
    if (firstInvalid) {
      document.getElementById(`checkout-${firstInvalid}`)?.focus()
    }
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

  const fieldProps = (field) => ({
    id: `checkout-${field}`,
    value: form[field],
    onChange: updateField(field),
    'aria-invalid': errors[field] ? 'true' : 'false',
    'aria-describedby': errors[field] ? `checkout-${field}-error` : undefined,
    className: 'lk-field',
  })

  const backLink = (
    <button
      type="button"
      onClick={() => navigate('/cart')}
      className="-ml-2 mb-1 flex min-h-11 items-center gap-1 px-2 text-[0.95rem] font-extrabold text-gold"
    >
      <ChevronLeftIcon />
      Корзина
    </button>
  )

  if (count === 0) {
    return (
      <main className="px-4 pt-3">
        {backLink}
        <PageHeader kicker="Доставка по России" title="Оформление" emblem={false} />
        <p className="mt-2 text-center text-sm text-cream-soft">Корзина пуста. Добавьте чай, чтобы оформить заказ.</p>
        <button type="button" onClick={() => navigate('/')} className="lk-btn mx-auto mt-6 max-w-[15rem]">
          К витрине
        </button>
      </main>
    )
  }

  return (
    <main className="px-4 pb-32 pt-3">
      {backLink}
      <PageHeader kicker="Доставка по России" title="Оформление" emblem={false} />

      <section aria-label="Ваш заказ" className="lk-card mt-3 flex flex-col gap-1.5 px-4 py-3">
        {items.map((item) => (
          <div key={item.id} className="flex justify-between gap-3 text-[0.95rem]">
            <span>
              {item.name} × {item.quantity}
            </span>
            <span className="flex-none font-bold">{formatPrice(item.line_total)}</span>
          </div>
        ))}
        <div className="my-1 h-px bg-lacquer-line" />
        <div className="flex items-baseline justify-between">
          <span className="lk-kicker">Итого · {formatPacks(count)}</span>
          <span className="font-display text-[1.625rem] text-gold">{formatPrice(total)}</span>
        </div>
      </section>

      <form id="checkout-form" noValidate className="mt-4 flex flex-col gap-3.5" onSubmit={handleSubmit}>
        <Field id="checkout-customer_name" label="Имя" error={errors.customer_name}>
          <input {...fieldProps('customer_name')} autoComplete="name" />
        </Field>
        <Field id="checkout-phone" label="Телефон" error={errors.phone}>
          <input {...fieldProps('phone')} type="tel" inputMode="tel" autoComplete="tel" placeholder="+79991234567" />
        </Field>
        <Field id="checkout-country" label="Страна" error={errors.country}>
          <div className="relative">
            <select {...fieldProps('country')}>
              <option value="Россия">Россия</option>
              <option value="other" disabled>
                Другие страны недоступны
              </option>
            </select>
            <ChevronDownIcon className="pointer-events-none absolute right-3.5 top-4 text-gold" />
          </div>
        </Field>
        <Field id="checkout-city" label="Город" error={errors.city}>
          <input {...fieldProps('city')} autoComplete="address-level2" />
        </Field>
        <Field id="checkout-address" label="Адрес" error={errors.address}>
          <textarea
            {...fieldProps('address')}
            className="lk-field min-h-[6rem] resize-none"
            autoComplete="street-address"
            placeholder="Улица, дом, квартира"
          />
        </Field>
      </form>

      <div
        className="fixed bottom-0 left-1/2 z-30 w-full max-w-[var(--app-width)] -translate-x-1/2 border-t border-lacquer-line bg-lacquer-deep px-4 pt-3"
        style={{ paddingBottom: 'calc(1rem + var(--safe-bottom))' }}
      >
        <button type="submit" form="checkout-form" disabled={submitting} className="lk-btn">
          {submitting ? 'Отправляем…' : `Подтвердить заказ · ${formatPrice(total)}`}
        </button>
      </div>
    </main>
  )
}
