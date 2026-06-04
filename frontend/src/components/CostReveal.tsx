import type { HeroData, CostDriver } from '../types'
import { formatCurrency } from '../utils/format'

interface CostRevealProps {
  data: HeroData
  onComplete: () => void
}

interface DriverSection {
  key: string
  title: string
  explanation: string
  unitLabel: string
  volumeLabel: string
  source: string
}

const DRIVER_SECTIONS: DriverSection[] = [
  {
    key: 'ltl_reclass',
    title: 'LTL Freight Reclassification',
    explanation:
      'GDSN publishes inflated dimensions (13×11×7″) yielding density 37.98 lb/ft³ and freight class 55. Physical measurement yields 74.0 lb/ft³ and class 50. Carriers bill at the higher class.',
    unitLabel: '/case',
    volumeLabel: 'pallet shipments/yr',
    source:
      'LTL rates: Red Stag Fulfillment rate index, class 50=$18.00/cwt, class 55=$19.80/cwt',
  },
  {
    key: 'parcel_reweigh',
    title: 'Parcel Reweigh Back-Billing',
    explanation:
      'Shopify lists ship weight as 1.00 lb (unit net weight, not case gross). Actual parcel weighs 2.05 lb with DIM weight of 1.55 lb. Carriers bill at the greater: 3 lb.',
    unitLabel: '/shipment',
    volumeLabel: 'DTC orders/yr',
    source:
      'Parcel rates: FedEx/UPS 2026 standard list less 30% volume discount',
  },
  {
    key: 'compliance_cb',
    title: 'Compliance Chargebacks',
    explanation:
      'Published dimensions do not match physical measurement. When a retailer DC flags the mismatch, the chargeback is assessed per event.',
    unitLabel: '/event',
    volumeLabel: 'events/yr',
    source:
      'Chargeback estimate: Walmart SQEP benchmarks via Surpass Solutions',
  },
]

function DriverCard({ section, driver }: { section: DriverSection; driver: CostDriver }) {
  return (
    <section className="cost-driver" aria-labelledby={`driver-${section.key}`}>
      <h3 id={`driver-${section.key}`} className="cost-driver__title">
        {section.title}
      </h3>
      <p className="cost-driver__explanation">{section.explanation}</p>
      <p className="cost-driver__math">
        {formatCurrency(driver.per_unit_delta)}
        {section.unitLabel} &times; {driver.annual_units} {section.volumeLabel} ={' '}
        <span className="cost-driver__annual">{formatCurrency(driver.annual_cost)}/yr</span>
      </p>
      <p className="cost-driver__source">{section.source}</p>
    </section>
  )
}

export default function CostReveal({ data, onComplete }: CostRevealProps) {
  const totalAnnualCost = Object.values(data.cost).reduce(
    (sum, d) => sum + d.annual_cost,
    0,
  )

  return (
    <div className="cost-reveal">
      {DRIVER_SECTIONS.map((section, i) => {
        const driver = data.cost[section.key]
        if (!driver) return null
        return (
          <div key={section.key}>
            <DriverCard section={section} driver={driver} />
            {i < DRIVER_SECTIONS.length - 1 && <hr className="cost-reveal__divider" />}
          </div>
        )
      })}

      <div className="cost-reveal__total">
        <p className="cost-reveal__total-amount">
          {formatCurrency(totalAnnualCost)} per year
        </p>
        <p className="cost-reveal__total-qualifier">for one SKU.</p>
      </div>

      <div className="cost-reveal__actions">
        <button className="btn-primary" onClick={onComplete}>
          Continue
        </button>
      </div>
    </div>
  )
}
