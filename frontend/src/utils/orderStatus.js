export const STATUS_RANK = {
  new: 0,
  in_progress: 1,
  packed: 2,
  shipped: 3,
  done: 4,
}

export const PROGRESS_STEPS = 4

const PILL_CLASSES = {
  shipped: 'bg-gold text-lacquer',
  done: 'border-[1.5px] border-sage text-sage',
  cancelled: 'bg-lacquer-raised text-cream-muted',
}

export function statusPillClass(status) {
  return PILL_CLASSES[status] ?? 'border-[1.5px] border-gold text-gold'
}

export function hasTracking(order) {
  return Boolean(order.tracking_number) && (order.status === 'shipped' || order.status === 'done')
}
