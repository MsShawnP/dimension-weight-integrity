import type { HeroData } from '../types'
import { formatCurrency } from '../utils/format'

interface GovernanceResolutionProps {
  data: HeroData
}

export default function GovernanceResolution({ data }: GovernanceResolutionProps) {
  const baseLtl = data.cost['ltl_reclass']?.annual_cost ?? 0
  const baseCb = data.cost['compliance_cb']?.annual_cost ?? 0
  const baseParcel = data.cost['parcel_reweigh']?.annual_cost ?? 0
  const baseTotal = baseLtl + baseCb + baseParcel

  return (
    <section className="resolution-view">
      <h2 className="resolution-title">The Resolution: Governed Measurement of Record</h2>
      <p className="resolution-intro">
        The WMS physical measurement becomes the single source of truth — the
        Measurement of Record. When GDSN, ERP, and Shopify all reference it,
        freight class aligns to physics, parcel weights match actual shipments,
        and compliance chargebacks disappear. Both channels clear simultaneously.
      </p>

      <div className="resolution-channels">
        <div className="paradox-channel paradox-channel--fixed">
          <h3 className="paradox-channel__title">Retail / LTL Channel</h3>
          <div className="paradox-channel__row">
            <span className="paradox-channel__label">LTL reclass cost</span>
            <span className="paradox-channel__cost">{formatCurrency(0)}</span>
          </div>
          <div className="paradox-channel__row">
            <span className="paradox-channel__label">Compliance chargebacks</span>
            <span className="paradox-channel__cost">{formatCurrency(0)}</span>
          </div>
          <span className="paradox-channel__status">Fixed</span>
        </div>

        <div className="paradox-channel paradox-channel--fixed">
          <h3 className="paradox-channel__title">DTC / Parcel Channel</h3>
          <div className="paradox-channel__row">
            <span className="paradox-channel__label">Parcel reweigh cost</span>
            <span className="paradox-channel__cost">{formatCurrency(0)}</span>
          </div>
          <span className="paradox-channel__status">Fixed</span>
        </div>
      </div>

      <div className="resolution-summary">
        <div className="resolution-summary__before">
          <span className="resolution-summary__label">Before: divergent systems</span>
          <span className="resolution-summary__value resolution-summary__value--before">
            {formatCurrency(baseTotal)}
          </span>
        </div>
        <div className="resolution-summary__after">
          <span className="resolution-summary__label">After: governed MoR</span>
          <span className="resolution-summary__value resolution-summary__value--after">
            {formatCurrency(0)}
          </span>
        </div>
      </div>

      <p className="resolution-insight">
        A governed measurement of record is the only configuration that clears
        both channels. No per-channel fix can.
      </p>
    </section>
  )
}
