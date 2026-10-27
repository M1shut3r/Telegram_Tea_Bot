import { CheckIcon } from './Icons'

const NOTES = {
  in_progress: 'Готовим ваш заказ',
  packed: 'Посылка упакована',
  shipped: 'Следите по трек-номеру',
  done: 'Приятного чаепития!',
}

export default function OrderRoadmap({ stages }) {
  const nextIndex = stages.findIndex((stage) => !stage.done)

  return (
    <section aria-label="Этапы заказа" className="lk-card p-4">
      <ol className="flex flex-col">
        {stages.map((stage, index) => {
          const isNext = index === nextIndex
          const isLast = index === stages.length - 1
          const nextDone = !isLast && stages[index + 1].done
          return (
            <li key={stage.status} className="flex gap-3.5">
              <div className="flex flex-col items-center">
                {stage.done ? (
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gold text-lacquer">
                    <CheckIcon />
                  </span>
                ) : (
                  <span
                    className={[
                      'flex h-8 w-8 items-center justify-center rounded-full border-[1.5px] text-[13px] font-extrabold text-cream-dim',
                      isNext ? 'border-gold' : 'border-lacquer-line',
                    ].join(' ')}
                  >
                    {index + 1}
                  </span>
                )}
                {isLast ? null : (
                  <span aria-hidden="true" className={['h-[22px] w-0.5', nextDone ? 'bg-gold' : 'bg-lacquer-line'].join(' ')} />
                )}
              </div>
              <div className="flex flex-col pt-[5px]">
                <span
                  className={[
                    'text-base',
                    stage.done || isNext ? 'font-extrabold text-cream' : 'font-semibold text-cream-dim',
                  ].join(' ')}
                >
                  {stage.title}
                  <span className="sr-only">{stage.done ? ' — пройдено' : ' — впереди'}</span>
                </span>
                {NOTES[stage.status] ? <span className="text-xs text-cream-dim">{NOTES[stage.status]}</span> : null}
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
