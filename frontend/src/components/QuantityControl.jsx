import { MinusIcon, PlusIcon } from './Icons'

// 0 шт. — красная кнопка «В корзину», иначе — золотой степпер «− N шт. +».
export default function QuantityControl({
  quantity,
  busy,
  onIncrement,
  onDecrement,
  name = '',
  tall = false,
  addLabel = 'В корзину',
}) {
  const height = tall ? 'min-h-[3.25rem]' : 'min-h-[2.75rem]'

  if (quantity <= 0) {
    return (
      <button type="button" disabled={busy} onClick={onIncrement} className={`lk-btn ${height} text-[0.95rem]`}>
        {addLabel}
      </button>
    )
  }

  const suffix = name ? ` «${name}»` : ''
  return (
    <div className={`lk-stepper ${height}`}>
      <button type="button" disabled={busy} onClick={onDecrement} aria-label={`Убрать одну пачку${suffix}`}>
        <MinusIcon />
      </button>
      <span className="text-[0.95rem] font-extrabold" aria-live="polite">
        {quantity} шт.
      </span>
      <button type="button" disabled={busy} onClick={onIncrement} aria-label={`Добавить пачку${suffix}`}>
        <PlusIcon />
      </button>
    </div>
  )
}
