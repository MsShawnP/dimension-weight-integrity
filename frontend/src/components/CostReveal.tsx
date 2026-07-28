import type { HeroData, CostDriver } from '../types'
import { formatCount, formatCurrency, formatDimension, formatWeight } from '../utils/format'

interface CostRevealProps {
  data: HeroData
  onComplete: () => void
}

interface DriverSection {
  key: string
  title: string
  // Built from the driver's own `basis`, which the pipeline ships alongside
  // every cost. Hard-coding these figures let the prose drift from the data.
  explain: (basis: Record<string, unknown>, data: HeroData) => string
  unitLabel: string
  volumeLabel: string
  source: string
}

function num(basis: Record<string, unknown>, key: string): number | null {
  const value = basis[key]
  return typeof value === 'number' ? value : null
}

/** GDSN's published case dimensions, read from the hero's divergence rows. */
function gdsnDims(data: HeroData): string | null {
  const gdsn = data.hero_sku.systems.find(s => s.system === 'gdsn')
  if (!gdsn) return null
  const value = (field: string) => gdsn.divergences.find(d => d.field === field)?.system_value
  const l = value('case_length_in')
  const w = value('case_width_in')
  const h = value('case_height_in')
  if (l == null || w == null || h == null) return null
  return `${formatDimension(l)} × ${formatDimension(w)} × ${formatDimension(h)}`
}

const DRIVER_SECTIONS: DriverSection[] = [
  {
    key: 'ltl_reclass',
    title: 'LTL Freight Reclassification',
    explain: (basis, data) => {
      const dims = gdsnDims(data)
      const density = (key: string) => {
        const value = num(basis, key)
        return value == null ? '—' : value.toFixed(2)
      }
      return [
        `GDSN publishes inflated dimensions${dims ? ` (${dims})` : ''} yielding density`,
        `${density('gdsn_density')} lb/ft³ and freight class ${num(basis, 'gdsn_class')}.`,
        `Physical measurement yields ${density('mor_density')} lb/ft³ and class`,
        `${num(basis, 'mor_class')}. Carriers bill at the higher class.`,
      ].join(' ')
    },
    unitLabel: '/case',
    // LTL bills per hundredweight, so the reclass delta is priced per case
    // against annual case volume. How cases stack on a pallet cancels out.
    volumeLabel: 'cases/yr',
    source:
      'LTL rates: modeled stand-in — class 50=$18.00/cwt, class 55=$19.80/cwt. Per-class step sized from published 15–25%-per-step benchmarks (Red Stag, Jansson LLC).',
  },
  {
    key: 'parcel_reweigh',
    title: 'Parcel Reweigh Back-Billing',
    explain: (basis) => {
      const shopify = num(basis, 'shopify_weight_lb')
      const gross = num(basis, 'dtc_parcel_gross_lb')
      const dim = num(basis, 'dim_weight_lb')
      return [
        `Shopify lists ship weight as ${shopify == null ? '—' : formatWeight(shopify)}`,
        `(unit net weight, not case gross). Actual parcel weighs`,
        `${gross == null ? '—' : formatWeight(gross)} with DIM weight of`,
        `${dim == null ? '—' : formatWeight(dim)}. Carriers bill at the greater:`,
        `${num(basis, 'billable_weight_lb')} lb.`,
      ].join(' ')
    },
    unitLabel: '/shipment',
    volumeLabel: 'DTC orders/yr',
    source:
      'Parcel rates: FedEx Ground Zone 5 2026 published list, modeled at a ~30% negotiated discount',
  },
  {
    key: 'compliance_cb',
    title: 'Compliance Chargebacks',
    explain: () =>
      'Published dimensions do not match physical measurement. When a retailer DC flags the mismatch, the chargeback is assessed per event.',
    unitLabel: '/event',
    volumeLabel: 'events/yr',
    source:
      'Chargeback estimate: Walmart SQEP benchmarks via Surpass Solutions',
  },
]

function DriverCard({ section, driver, data }: { section: DriverSection; driver: CostDriver; data: HeroData }) {
  return (
    <section className="cost-driver" aria-labelledby={`driver-${section.key}`}>
      <h3 id={`driver-${section.key}`} className="cost-driver__title">
        {section.title}
      </h3>
      <p className="cost-driver__explanation">{section.explain(driver.basis ?? {}, data)}</p>
      <p className="cost-driver__math">
        {formatCurrency(driver.per_unit_delta)}
        {section.unitLabel} &times; {formatCount(driver.annual_units)} {section.volumeLabel} ={' '}
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
            <DriverCard section={section} driver={driver} data={data} />
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
