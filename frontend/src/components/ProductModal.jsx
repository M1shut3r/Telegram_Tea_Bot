import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import emblemUrl from '../assets/logo-emblem.svg'
import { formatPrice } from '../utils/format'
import { CartIcon, ChevronLeftIcon } from './Icons'
import { BerryDivider, Sprig } from './Ornaments'
import QuantityControl from './QuantityControl'

export default function ProductModal({ product, quantity, busy, onClose, onIncrement, onDecrement, onGoToCart }) {
  const [broken, setBroken] = useState(false)
  const dialogRef = useRef(null)
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  const isOpen = product != null

  useEffect(() => {
    setBroken(false)
  }, [product?.id])

  useEffect(() => {
    if (!isOpen) {
      return undefined
    }
    const scroller = document.querySelector('.tg-scroll')
    const previousOverflow = scroller ? scroller.style.overflow : ''
    const previousFocus = document.activeElement
    document.body.classList.add('sheet-open')
    if (scroller) {
      scroller.style.overflow = 'hidden'
    }
    dialogRef.current?.focus()
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        closeRef.current()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.classList.remove('sheet-open')
      if (scroller) {
        scroller.style.overflow = previousOverflow
      }
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus()
      }
    }
  }, [isOpen])

  if (product == null) {
    return null
  }

  return createPortal(
    <div
      ref={dialogRef}
      tabIndex={-1}
      className="product-sheet outline-none"
      role="dialog"
      aria-modal="true"
      aria-labelledby="product-sheet-title"
    >
      <div className="flex flex-none items-center justify-between px-2 pt-2">
        <button
          type="button"
          onClick={onClose}
          className="flex min-h-11 items-center gap-1 px-2 text-[0.95rem] font-extrabold text-gold"
        >
          <ChevronLeftIcon />
          Витрина
        </button>
        <button
          type="button"
          onClick={onGoToCart}
          aria-label="Корзина"
          className="flex h-11 w-11 items-center justify-center text-gold"
        >
          <CartIcon />
        </button>
      </div>

      <div className="product-sheet-scroll">
        <div className="flex flex-col gap-[1.125rem] px-4 pb-6 pt-1.5">
          <div className="lk-card relative flex justify-center overflow-hidden rounded-[1.25rem] py-6">
            <Sprig className="absolute left-1.5 top-10" />
            <Sprig mirrored className="absolute right-1.5 top-10" />
            <span className="lk-photo relative block aspect-[2/3] w-[164px] rounded-[0.625rem] [box-shadow:0_0_0_4px_#211813,0_0_0_6px_#b8321f]">
              {broken ? (
                <span className="flex h-full items-center justify-center">
                  <img src={emblemUrl} alt="" className="w-3/4 opacity-80" />
                </span>
              ) : (
                <img
                  src={product.photo_url}
                  alt={`Упаковка чая «${product.name}»`}
                  className="h-full w-full object-cover"
                  onError={() => setBroken(true)}
                />
              )}
            </span>
          </div>

          <div className="flex flex-col items-center gap-1 text-center">
            <p className="lk-kicker">Коллекция «Жили-Пили»</p>
            <h2 id="product-sheet-title" className="font-display text-[2.375rem] leading-tight text-cream">
              {product.name}
            </h2>
            <p className="text-2xl font-extrabold text-gold">{formatPrice(product.price)}</p>
            <BerryDivider className="mt-1.5" />
          </div>

          {product.description ? (
            <p className="whitespace-pre-line text-center text-base leading-relaxed text-[#e8dcc8]">{product.description}</p>
          ) : null}

          {product.composition ? (
            <section aria-labelledby="product-sheet-composition" className="lk-card flex flex-col gap-1.5 px-4 py-3.5">
              <h3 id="product-sheet-composition" className="lk-kicker text-gold">
                Состав
              </h3>
              <p className="whitespace-pre-line text-base leading-relaxed">{product.composition}</p>
            </section>
          ) : null}
        </div>
      </div>

      <div className="product-sheet-actions">
        {quantity > 0 ? (
          <div className="flex gap-2.5">
            <div className="w-[9.25rem] flex-none">
              <QuantityControl
                quantity={quantity}
                busy={busy}
                tall
                onIncrement={() => onIncrement(product)}
                onDecrement={() => onDecrement(product)}
              />
            </div>
            <button type="button" onClick={onGoToCart} className="lk-btn-gold">
              В корзине · {formatPrice(Number(product.price) * quantity)}
            </button>
          </div>
        ) : (
          <QuantityControl
            quantity={quantity}
            busy={busy}
            tall
            addLabel={`В корзину · ${formatPrice(product.price)}`}
            onIncrement={() => onIncrement(product)}
            onDecrement={() => onDecrement(product)}
          />
        )}
      </div>
    </div>,
    document.body,
  )
}
