import NeonSign from './NeonSign'

export default function MaisonHeader({ kicker, title, children }) {
  return (
    <header className="mb-8 pt-3 text-center">
      <NeonSign />
      {kicker ? <p className="maison-kicker mt-5">{kicker}</p> : null}
      <h1 className="maison-title">{title}</h1>
      <div className="maison-rule" />
      {children ? <div className="mx-auto mt-4 max-w-xs text-sm font-light leading-relaxed text-tg-hint">{children}</div> : null}
    </header>
  )
}
