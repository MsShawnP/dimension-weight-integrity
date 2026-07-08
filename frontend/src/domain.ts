export function cubeFt3(lengthIn: number, widthIn: number, heightIn: number): number {
  return (lengthIn * widthIn * heightIn) / 1728
}

export function densityLbPerFt3(weightLb: number, cubeFt3: number): number {
  return weightLb / cubeFt3
}

// NMFC density-based classification — the 18 standard freight classes.
// Lower-bound (>=) breakpoints, density in lb/ft^3 (pcf). Must stay in
// lockstep with dbt/macros/density_to_nmfc_class.sql.
const NMFC_BANDS: [number, number][] = [
  [50.0, 50], [35.0, 55], [30.0, 60], [22.5, 65],
  [15.0, 70], [13.5, 77.5], [12.0, 85], [10.5, 92.5],
  [9.0, 100], [8.0, 110], [7.0, 125], [6.0, 150],
  [5.0, 175], [4.0, 200], [3.0, 250], [2.0, 300],
  [1.0, 400],
]

export function densityToNmfcClass(density: number): number {
  for (const [threshold, nmfcClass] of NMFC_BANDS) {
    if (density >= threshold) return nmfcClass
  }
  return 500
}

export function dimWeightLb(lengthIn: number, widthIn: number, heightIn: number, divisor: number): number {
  return (Math.ceil(lengthIn) * Math.ceil(widthIn) * Math.ceil(heightIn)) / divisor
}

export function billableWeightLb(actualWeight: number, dimWeight: number): number {
  return Math.ceil(Math.max(actualWeight, dimWeight))
}

function lookupRate(rates: Record<string, number>, key: number): number {
  return rates[String(key)] ?? 0
}

export function computeLtlDelta(
  gdsnClass: number,
  morClass: number,
  caseWeightLb: number,
  rates: Record<string, number>
): number {
  if (gdsnClass === morClass) return 0
  const gdsnRate = lookupRate(rates, gdsnClass)
  const morRate = lookupRate(rates, morClass)
  // Floor at 0: a downward class shift triggers a carrier reweigh/back-bill,
  // never a saving. Never book a negative reclassification cost.
  return Math.max(0, (caseWeightLb / 100) * (gdsnRate - morRate))
}

export function computeParcelDelta(
  billableWeight: number,
  shopifyWeight: number,
  rates: Record<string, number>
): number {
  const billableRate = lookupRate(rates, billableWeight)
  const shopifyRate = lookupRate(rates, Math.ceil(shopifyWeight))
  return Math.max(0, billableRate - shopifyRate)
}

export interface ParadoxResult {
  ltlCost: number
  parcelCost: number
  cbCost: number
  ltlFixed: boolean
  parcelFixed: boolean
}

export function computeParadox(
  fixType: 'none' | 'ops' | 'dtc',
  baseCosts: { ltl: number; parcel: number; cb: number }
): ParadoxResult {
  if (fixType === 'none') {
    return { ltlCost: baseCosts.ltl, parcelCost: baseCosts.parcel, cbCost: baseCosts.cb, ltlFixed: false, parcelFixed: false }
  }

  if (fixType === 'ops') {
    return {
      ltlCost: 0,
      parcelCost: baseCosts.parcel,
      cbCost: 0,
      ltlFixed: true,
      parcelFixed: false,
    }
  }

  // DTC fix: parcel fixed, but quoted price rises for customer
  return {
    ltlCost: baseCosts.ltl,
    parcelCost: 0,
    cbCost: baseCosts.cb,
    ltlFixed: false,
    parcelFixed: true,
  }
}
