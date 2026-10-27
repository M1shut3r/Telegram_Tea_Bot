function Svg({ size = 22, strokeWidth = 1.8, children, className }) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {children}
    </svg>
  )
}

export function CatalogIcon(props) {
  return (
    <Svg {...props}>
      <rect x="4" y="4" width="7" height="7" rx="2" />
      <rect x="13" y="4" width="7" height="7" rx="2" />
      <rect x="4" y="13" width="7" height="7" rx="2" />
      <rect x="13" y="13" width="7" height="7" rx="2" />
    </Svg>
  )
}

export function CartIcon(props) {
  return (
    <Svg {...props}>
      <path d="M3 4h2l2.4 10.2a1 1 0 0 0 1 .8h8.8a1 1 0 0 0 1-.8L20 7H6" />
      <circle cx="9" cy="19.5" r="1.3" />
      <circle cx="17" cy="19.5" r="1.3" />
    </Svg>
  )
}

export function OrdersIcon(props) {
  return (
    <Svg {...props}>
      <path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" />
      <path d="M9 8h6M9 12h6M9 16h3" />
    </Svg>
  )
}

export function PlusIcon(props) {
  return (
    <Svg size={18} strokeWidth={2.2} {...props}>
      <path d="M12 5v14M5 12h14" />
    </Svg>
  )
}

export function MinusIcon(props) {
  return (
    <Svg size={18} strokeWidth={2.2} {...props}>
      <path d="M5 12h14" />
    </Svg>
  )
}

export function TrashIcon(props) {
  return (
    <Svg size={20} {...props}>
      <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6" />
    </Svg>
  )
}

export function ChevronLeftIcon(props) {
  return (
    <Svg size={20} strokeWidth={2} {...props}>
      <path d="M15 5l-7 7 7 7" />
    </Svg>
  )
}

export function ChevronRightIcon(props) {
  return (
    <Svg size={18} strokeWidth={2.4} {...props}>
      <path d="M9 5l7 7-7 7" />
    </Svg>
  )
}

export function ChevronDownIcon(props) {
  return (
    <Svg size={18} strokeWidth={2} {...props}>
      <path d="M6 9l6 6 6-6" />
    </Svg>
  )
}

export function CloseIcon(props) {
  return (
    <Svg size={20} strokeWidth={2} {...props}>
      <path d="M6 6l12 12M18 6L6 18" />
    </Svg>
  )
}

export function CheckIcon(props) {
  return (
    <Svg size={16} strokeWidth={3} {...props}>
      <path d="M5 12l5 5 9-10" />
    </Svg>
  )
}

export function ParcelIcon(props) {
  return (
    <Svg size={16} {...props}>
      <path d="M3 7l9-4 9 4v10l-9 4-9-4z" />
      <path d="M3 7l9 4 9-4M12 11v10" />
    </Svg>
  )
}

export function CancelledIcon(props) {
  return (
    <Svg size={20} strokeWidth={2} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 8l8 8M16 8l-8 8" />
    </Svg>
  )
}
