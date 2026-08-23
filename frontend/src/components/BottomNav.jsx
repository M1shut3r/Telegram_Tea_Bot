import { NavLink } from 'react-router-dom'
import { useCart } from '../context/CartContext'

function CatalogIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.4">
      <rect x="4" y="4" width="7" height="7" />
      <rect x="13" y="4" width="7" height="7" />
      <rect x="4" y="13" width="7" height="7" />
      <rect x="13" y="13" width="7" height="7" />
    </svg>
  )
}

function CartIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.4">
      <path d="M5 7h15l-1.3 8.4H8.1L5 4H3" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="9.5" cy="19.2" r="1.15" fill="currentColor" stroke="none" />
      <circle cx="16.5" cy="19.2" r="1.15" fill="currentColor" stroke="none" />
    </svg>
  )
}

function OrdersIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.4">
      <path d="M7 4h10v16l-5-2.4L7 20V4Z" strokeLinejoin="round" />
      <path d="M10 9h4M10 13h3" strokeLinecap="round" />
    </svg>
  )
}

const items = [
  { to: '/', label: 'Витрина', icon: CatalogIcon, end: true },
  { to: '/cart', label: 'Корзина', icon: CartIcon, end: false },
  { to: '/orders', label: 'Заказы', icon: OrdersIcon, end: false },
]

export default function BottomNav() {
  const { count } = useCart()

  return (
    <nav className="maison-dock fixed bottom-0 z-30 backdrop-blur-xl">
      <div className="grid grid-cols-3 px-3 pb-[max(0.65rem,env(safe-area-inset-bottom))] pt-2.5">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                [
                  'relative flex flex-col items-center gap-1 px-2 py-1.5 text-[10px] font-medium uppercase tracking-[0.18em] transition',
                  isActive ? 'text-neon' : 'text-cream/40',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  {isActive ? <span className="absolute inset-x-6 -top-2.5 h-px bg-neon/80" /> : null}
                  <span className="relative">
                    <Icon />
                    {item.to === '/cart' && count > 0 ? (
                      <span className="absolute -right-2.5 -top-1.5 min-w-[16px] bg-neon px-1 text-center text-[9px] font-semibold leading-[16px] text-night">
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
