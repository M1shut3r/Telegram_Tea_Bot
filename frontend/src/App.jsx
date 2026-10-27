import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import Cart from './pages/Cart'
import Catalog from './pages/Catalog'
import Checkout from './pages/Checkout'
import Orders from './pages/Orders'

export default function App() {
  const location = useLocation()
  const hideNav = location.pathname === '/checkout'

  return (
    <div className="tg-shell text-cream">
      <div className="tg-scroll">
        <div className={hideNav ? '' : 'pb-[calc(var(--dock-height)+var(--safe-bottom)+1.5rem)]'}>
          <Routes>
            <Route path="/" element={<Catalog />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
      {hideNav ? null : <BottomNav />}
    </div>
  )
}
