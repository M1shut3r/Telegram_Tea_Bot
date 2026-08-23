import { NavLink } from 'react-router-dom'
import { useCart } from '../context/CartContext'

function CatalogIcon({ active }) {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.7">
      <rect x="3.5" y="3.5" width="7" height="7" rx="2" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="2" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="2" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="2" className={active ? 'opacity-100' : 'opacity-80'} />
    </svg>
  )
}

function CartIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M6 7h15l-1.4 8.2a2 2 0 0 1-2 1.6H9.2a2 2 0 0 1-2-1.5L5.2 4H3" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="10" cy="20" r="1.2" fill="currentColor" stroke="none" />
      <circle cx="17" cy="20" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  )
}

function OrdersIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M7 4h10a2 2 0 0 1 2 2v14l-3.2-2-3.8 2-3.8-2L5 20V6a2 2 0 0 1 2-2Z" strokeLinejoin="round" />
      <path d="M9 9h6M9 13h4" strokeLinecap="round" />
    </svg>
  )
}

const items = [
  { to: '/', label: 'Каталог', icon: CatalogIcon, end: true },
  { to: '/cart', label: 'Корзина', icon: CartIcon, end: false },
  { to: '/orders', label: 'Заказы', icon: OrdersIcon, end: false },
]

export default function BottomNav() {
  const { count } = useCart()

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-black/5 bg-tg-bg/90 backdrop-blur-xl">
      <div className="mx-auto grid max-w-lg grid-cols-3 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                [
                  'relative flex flex-col items-center gap-1 rounded-2xl px-2 py-1.5 text-[11px] font-medium tracking-wide transition',
                  isActive ? 'text-tg-button' : 'text-tg-hint',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  <span className="relative">
                    <Icon active={isActive} />
                    {item.to === '/cart' && count > 0 ? (
                      <span className="absolute -right-2.5 -top-1.5 min-w-[18px] rounded-full bg-tg-button px-1 text-center text-[10px] font-semibold leading-[18px] text-tg-button-text">
                        {count}
                      </span>
                    ) : null}
                  </span>
                  {item.label}
                </>
              )}
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
