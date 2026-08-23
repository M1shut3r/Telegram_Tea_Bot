export default function OrderRoadmap({ stages }) {
  return (
    <ol className="maison-card px-4 py-4">
      {stages.map((stage, index) => (
        <li key={stage.status}>
          {index > 0 ? (
            <div className="flex justify-center py-1">
              <span className={stage.done ? 'text-neon/70' : 'text-tg-hint/40'}>│</span>
            </div>
          ) : null}
          <div className="flex items-center gap-3 py-1">
            <span
              className={[
                'flex h-8 w-8 shrink-0 items-center justify-center border text-[11px] uppercase tracking-[0.12em]',
                stage.done ? 'border-neon/50 bg-night text-neon' : 'border-white/10 text-tg-hint',
              ].join(' ')}
            >
              {stage.done ? '✓' : index + 1}
            </span>
            <span className={stage.done ? 'font-medium' : 'font-light text-tg-hint'}>{stage.title}</span>
          </div>
        </li>
      ))}
    </ol>
  )
}
