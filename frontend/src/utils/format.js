export function formatPrice(value) {
  const number = Number(value)
  if (Number.isNaN(number)) {
    return '0 ₽'
  }
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: number % 1 === 0 ? 0 : 2,
  }).format(number)
}

export function pluralize(count, [one, few, many]) {
  const n = Math.abs(Number(count)) % 100
  const n10 = n % 10
  if (n10 === 1 && n !== 11) {
    return one
  }
  if (n10 >= 2 && n10 <= 4 && (n < 12 || n > 14)) {
    return few
  }
  return many
}

export function formatPacks(count) {
  return `${count} ${pluralize(count, ['пачка', 'пачки', 'пачек'])}`
}

export function formatDate(value) {
  if (!value) {
    return ''
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
