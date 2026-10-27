import feastUrl from '../assets/feast.jpg'

const KOKOSHNIK_PATH = 'M0 236L0 96C0 70 18 58 52 52C110 42 150 26 179 0C208 26 248 42 306 52C340 58 358 70 358 96L358 236Z'

// Тонкая золотая линия с гроздью ягод — разделитель под заголовками.
export function BerryDivider({ width = 200, className = '' }) {
  return (
    <svg aria-hidden="true" width={width} height="18" viewBox="0 0 240 18" fill="none" className={className}>
      <path d="M0 9h96M144 9h96" stroke="#8a6a35" strokeWidth="1.4" />
      <circle cx="111" cy="10" r="5" fill="#b8321f" />
      <circle cx="129" cy="10" r="5" fill="#b8321f" />
      <circle cx="120" cy="4" r="4.5" fill="#d6452e" />
      <circle cx="102" cy="9" r="2" fill="#dda94a" />
      <circle cx="138" cy="9" r="2" fill="#dda94a" />
    </svg>
  )
}

// Хохломская веточка с ягодами — обрамляет фото пачки в карточке.
export function Sprig({ mirrored = false, className = '' }) {
  return (
    <svg
      aria-hidden="true"
      width="70"
      height="200"
      viewBox="0 0 70 200"
      fill="none"
      className={className}
      style={mirrored ? { transform: 'scaleX(-1)' } : undefined}
    >
      <path d="M8 196C20 150 14 110 34 70C44 50 48 30 40 8" stroke="#c39340" strokeWidth="2.2" strokeLinecap="round" />
      <path
        d="M34 70c12-4 20-14 20-26-12 2-18 12-20 26zM24 120c-12-2-18-10-18-20 10 2 16 10 18 20zM40 8c-10 2-14 10-12 18 8-4 12-10 12-18z"
        fill="#c39340"
      />
      <circle cx="46" cy="96" r="7" fill="#c63d2b" />
      <circle cx="34" cy="104" r="6" fill="#c63d2b" />
      <circle cx="18" cy="160" r="6" fill="#c63d2b" />
      <circle cx="44" cy="94" r="2" fill="#f4ecdf" />
    </svg>
  )
}

// Застолье с упаковки в рамке-кокошнике (пустая корзина).
export function KokoshnikFeast({ className = '' }) {
  return (
    <svg
      viewBox="-10 -10 378 256"
      className={className}
      role="img"
      aria-label="Семья пьёт чай за самоваром — иллюстрация с упаковки"
    >
      <defs>
        <clipPath id="lk-kokoshnik-clip">
          <path d={KOKOSHNIK_PATH} />
        </clipPath>
      </defs>
      <g clipPath="url(#lk-kokoshnik-clip)">
        <rect x="0" y="0" width="358" height="236" fill="#f4ecdf" />
        <image href={feastUrl} x="0" y="54" width="358" height="182" preserveAspectRatio="xMidYMid slice" />
        <g transform="translate(119 22)" fill="none">
          <path
            d="M60 28C48 28 40 20 28 22C18 24 14 32 4 30M60 28c12 0 20-8 32-6 10 2 14 10 24 8"
            stroke="#b8862f"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <circle cx="52" cy="27" r="5" fill="#b8321f" />
          <circle cx="68" cy="27" r="5" fill="#b8321f" />
          <circle cx="60" cy="18" r="5" fill="#c63d2b" />
        </g>
      </g>
      <g fill="none">
        <path
          d={KOKOSHNIK_PATH}
          stroke="#b8321f"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
          transform="translate(-7 -7) scale(1.039 1.0593)"
        />
        <path d={KOKOSHNIK_PATH} stroke="#dda94a" strokeWidth="5" />
        <path
          d={KOKOSHNIK_PATH}
          stroke="#dda94a"
          strokeWidth="1.2"
          vectorEffect="non-scaling-stroke"
          transform="translate(9 9) scale(0.9497 0.9237)"
        />
      </g>
    </svg>
  )
}
