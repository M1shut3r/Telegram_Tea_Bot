export default function OrderRoadmap({ stages }) {
  return (
    <ol className="space-y-0">
      {stages.map((stage, index) => (
        <li key={stage.status}>
          {index > 0 ? (
            <div className="flex justify-center py-1">
              <span className={stage.done ? 'text-tg-button' : 'text-tg-hint'}>↓</span>
            </div>
          ) : null}
          <div className="flex items-center gap-3 rounded-2xl bg-tg-bg px-4 py-3">
            <span
              className={[
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold',
                stage.done ? 'bg-tg-button text-tg-button-text' : 'bg-tg-secondary text-tg-hint',
              ].join(' ')}
            >
              {stage.done ? '✓' : index + 1}
            </span>
            <span className={stage.done ? 'font-semibold' : 'text-tg-hint'}>{stage.title}</span>
          </div>
        </li>
      ))}
    </ol>
  )
}
