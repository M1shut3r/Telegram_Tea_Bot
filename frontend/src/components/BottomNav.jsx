import { NavLink } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { formatPacks } from '../utils/format'
import { CartIcon, CatalogIcon, OrdersIcon } from './Icons'

const items = [
  { to: '/', label: 'Витрина', icon: CatalogIcon, end: true },
  { to: '/cart', label: 'Корзина', icon: CartIcon, end: false },
  { to: '/orders', label: 'Заказы', icon: OrdersIcon, end: false },
]

export default function BottomNav() {
  const { count } = useCart()

  return (
    <nav aria-label="Разделы магазина" className="lk-dock">
      <div className="grid grid-cols-3 px-2 pt-1.5" style={{ paddingBottom: 'calc(0.5rem + var(--safe-bottom))' }}>
        {items.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              aria-label={item.to === '/cart' && count > 0 ? `${item.label}: ${formatPacks(count)}` : undefined}
              className={({ isActive }) =>
                [
                  'flex min-h-[3.75rem] flex-col items-center justify-center gap-1 text-xs no-underline transition-colors',
                  isActive ? 'font-extrabold text-gold' : 'font-semibold text-cream-soft',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  <span className="relative flex">
                    <Icon />
                    {item.to === '/cart' && count > 0 ? (
                      <span
                        aria-hidden="true"
                        className="absolute -right-2.5 -top-1.5 min-w-[18px] rounded-full bg-cinnabar px-1 text-center text-[11px] font-extrabold leading-[18px] text-white"
                      >
                        {count}
                      </span>
                    ) : null}
                  </span>
                  <span>{item.label}</span>
                  <span
                    aria-hidden="true"
                    className={['h-1.5 w-1.5 rounded-full', isActive ? 'bg-cinnabar-bright' : 'bg-transparent'].join(' ')}
                  />
                </>
              )}
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
