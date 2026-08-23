export default function QuantityControl({ quantity, busy, onIncrement, onDecrement }) {
  if (quantity <= 0) {
    return (
      <button
        type="button"
        disabled={busy}
        onClick={onIncrement}
        className="flex h-11 w-full items-center justify-center rounded-2xl bg-tg-button text-lg font-semibold text-tg-button-text transition active:scale-[0.98] disabled:opacity-60"
      >
        +
      </button>
    )
  }

  return (
    <div className="flex h-11 w-full items-center justify-between rounded-2xl bg-tg-button px-1 text-tg-button-text">
      <button
        type="button"
        disabled={busy}
        onClick={onDecrement}
        className="flex h-8 w-8 items-center justify-center rounded-xl bg-black/10 text-base font-semibold disabled:opacity-60"
      >
        −
      </button>
      <span className="min-w-[1.5rem] text-center text-sm font-semibold">{quantity} шт</span>
      <button
        type="button"
        disabled={busy}
        onClick={onIncrement}
        className="flex h-9 w-9 items-center justify-center rounded-xl text-lg font-semibold disabled:opacity-60"
      >
        +
      </button>
    </div>
  )
}
