export default function QuantityControl({ quantity, busy, onIncrement, onDecrement, tall = false }) {
  const height = tall ? 'h-[3.25rem]' : 'h-11'

  if (quantity <= 0) {
    return (
      <button type="button" disabled={busy} onClick={onIncrement} className={`maison-btn ${height} text-[0.68rem]`}>
        В корзину
      </button>
    )
  }

  return (
    <div
      className={`flex w-full items-center justify-between border border-white/10 bg-forest px-1 text-cream ${height}`}
    >
      <button
        type="button"
        disabled={busy}
        onClick={onDecrement}
        className="flex h-11 w-11 items-center justify-center text-xl disabled:opacity-60"
      >
        −
      </button>
      <span className="min-w-[1.5rem] text-center text-[11px] font-medium uppercase tracking-[0.16em]">
        {quantity} шт
      </span>
      <button
        type="button"
        disabled={busy}
        onClick={onIncrement}
        className="flex h-11 w-11 items-center justify-center text-xl disabled:opacity-60"
      >
        +
      </button>
    </div>
  )
}
