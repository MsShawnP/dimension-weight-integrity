import { useState } from 'react'
import type { HeroData } from '../types'
import { computeParadox } from '../domain'
import { formatCurrency } from '../utils/format'

interface ParadoxToggleProps {
  data: HeroData
  onComplete: () => void
}

type FixType = 'none' | 'ops' | 'dtc'

const TOGGLE_LABELS: Record<FixType, string> = {
  none: 'Current State',
  ops: 'Fix Retail (Ops)',
  dtc: 'Fix DTC',
}

export default function ParadoxToggle({ data, onComplete }: ParadoxToggleProps) {
  const [fixType, setFixType] = useState<FixType>('none')

  const ltlReclass = data.cost['ltl_reclass']
  const parcelReweigh = data.cost['parcel_reweigh']
  const complianceCb = data.cost['compliance_cb']

  const baseCosts = {
    ltl: ltlReclass?.annual_cost ?? 0,
    parcel: parcelReweigh?.annual_cost ?? 0,
    cb: complianceCb?.annual_cost ?? 0,
  }

  const result = computeParadox(fixType, baseCosts)

  const totalRemaining = result.ltlCost + result.parcelCost + result.cbCost

  return (
    <section className="paradox-view">
      <h2 className="paradox-title">The Localization Paradox</h2>
      <p className="paradox-intro">
        Each channel&rsquo;s data can be corrected in isolation, but fixing one
        does not fix the other. Align GDSN dimensions to clear the retail
        freight-class error, and the DTC parcel leak persists. Correct Shopify
        weights to stop parcel back-billing, and the LTL overcharge and
        compliance chargebacks remain. No single-channel fix resolves both.
      </p>

      <div className="paradox-toggles" role="group" aria-label="Fix scenario">
        {(Object.keys(TOGGLE_LABELS) as FixType[]).map((key) => (
          <button
            key={key}
            type="button"
            className={`paradox-toggle-btn${fixType === key ? ' paradox-toggle-btn--active' : ''}`}
            onClick={() => setFixType(key)}
            aria-pressed={fixType === key}
          >
            {TOGGLE_LABELS[key]}
          </button>
        ))}
      </div>

      <div className="paradox-channels">
        <div
          className={`paradox-channel ${result.ltlFixed ? 'paradox-channel--fixed' : 'paradox-channel--warning'}`}
        >
          <h3 className="paradox-channel__title">Retail / LTL Channel</h3>
          <div className="paradox-channel__row">
            <span className="paradox-channel__label">LTL reclass cost</span>
            <span className="paradox-channel__cost">{formatCurrency(result.ltlCost)}</span>
          </div>
          <div className="paradox-channel__row">
            <span className="paradox-channel__label">Compliance chargebacks</span>
            <span className="paradox-channel__cost">{formatCurrency(result.cbCost)}</span>
          </div>
          <span className="paradox-channel__status">
            {result.ltlFixed ? 'Fixed' : 'Unresolved'}
          </span>
        </div>

        <div
          className={`paradox-channel ${result.parcelFixed ? 'paradox-channel--fixed' : 'paradox-channel--warning'}`}
        >
          <h3 className="paradox-channel__title">DTC / Parcel Channel</h3>
          <div className="paradox-channel__row">
            <span className="paradox-channel__label">Parcel reweigh cost</span>
            <span className="paradox-channel__cost">{formatCurrency(result.parcelCost)}</span>
          </div>
          <span className="paradox-channel__status">
            {result.parcelFixed ? 'Fixed' : 'Unresolved'}
          </span>
        </div>
      </div>

      <div className="paradox-summary">
        <span className="paradox-summary__label">Total remaining annual cost</span>
        <span className="paradox-summary__value">{formatCurrency(totalRemaining)}</span>
      </div>

      <div className="paradox-actions">
        <button type="button" className="btn-primary" onClick={onComplete}>
          Continue
        </button>
      </div>
    </section>
  )
}
