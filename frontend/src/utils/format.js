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
