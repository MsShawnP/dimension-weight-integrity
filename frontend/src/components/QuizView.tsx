import { useState } from 'react'
import type { HeroData, SystemData } from '../types'
import { formatWeight, formatDimension } from '../utils/format'

interface QuizViewProps {
  data: HeroData
  onComplete: () => void
}

const SYSTEM_DISPLAY_NAMES: Record<string, string> = {
  erp: 'NetSuite ERP',
  wms: '3PL / WMS',
  gdsn: 'GDSN (IX-ONE)',
  shopify: 'Shopify DTC',
}

const ANNOTATIONS: Record<string, string> = {
  erp: 'Net weight stored in gross field — biased low',
  wms: 'Physical measurement at receiving — the measurement of record',
  gdsn: 'Outer-box dims inflated for safe transit — overstates density',
  shopify: 'Unit net weight, not case gross — wildly understated',
}

function getWeight(sys: SystemData): number | null {
  const w =
    sys.divergences.find((d) => d.field === 'case_gross_weight_lb') ??
    sys.divergences.find((d) => d.field === 'ship_weight_lb')
  return w ? w.system_value : null
}

function getDims(sys: SystemData): { l: number; w: number; h: number } | null {
  const l = sys.divergences.find((d) => d.field === 'case_length_in')
  const w = sys.divergences.find((d) => d.field === 'case_width_in')
  const h = sys.divergences.find((d) => d.field === 'case_height_in')
  if (l && w && h) return { l: l.system_value, w: w.system_value, h: h.system_value }
  return null
}

export default function QuizView({ data, onComplete }: QuizViewProps) {
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null)
  const [revealed, setRevealed] = useState(false)

  const morSource = data.hero_sku.measurement_of_record.source
  const systems = data.hero_sku.systems

  function handleCardClick(systemKey: string) {
    if (revealed) return
    setSelectedSystem(systemKey)
  }

  function handleReveal() {
    if (!selectedSystem) return
    setRevealed(true)
  }

  function cardClassName(systemKey: string): string {
    const classes = ['quiz-card']
    if (!revealed && selectedSystem === systemKey) {
      classes.push('quiz-card--selected')
    }
    if (revealed) {
      if (systemKey === morSource) {
        classes.push('quiz-card--correct')
      } else {
        classes.push('quiz-card--wrong')
      }
    }
    return classes.join(' ')
  }

  return (
    <section className="quiz-view">
      <h2 className="quiz-title">Which system has the right weight?</h2>
      <p className="quiz-subtitle">
        Four systems store physical attributes for{' '}
        <strong>{data.hero_sku.product_name}</strong>. Pick the one you think
        matches reality.
      </p>

      <div className="quiz-grid">
        {systems.map((sys) => {
          const key = sys.system
          const weight = getWeight(sys)
          const dims = getDims(sys)

          return (
            <button
              key={key}
              type="button"
              className={cardClassName(key)}
              onClick={() => handleCardClick(key)}
              aria-pressed={!revealed && selectedSystem === key}
              disabled={revealed}
            >
              <span className="quiz-card__name">
                {SYSTEM_DISPLAY_NAMES[key] ?? key}
              </span>
              <span className="quiz-card__weight">
                {weight !== null ? formatWeight(weight) : '—'}
              </span>
              <span className="quiz-card__dims">
                {dims
                  ? `${formatDimension(dims.l)} × ${formatDimension(dims.w)} × ${formatDimension(dims.h)}`
                  : 'No dims published'}
              </span>
              {revealed && (
                <span className="quiz-card__annotation">
                  {ANNOTATIONS[key]}
                </span>
              )}
            </button>
          )
        })}
      </div>

      <div className="quiz-actions">
        {!revealed && (
          <button
            type="button"
            className="btn-primary"
            onClick={handleReveal}
            disabled={!selectedSystem}
          >
            Reveal
          </button>
        )}
        {revealed && (
          <button
            type="button"
            className="btn-primary"
            onClick={onComplete}
          >
            Continue
          </button>
        )}
      </div>
    </section>
  )
}
