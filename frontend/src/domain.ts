export function cubeFt3(lengthIn: number, widthIn: number, heightIn: number): number {
  return (lengthIn * widthIn * heightIn) / 1728
}

export function densityLbPerFt3(weightLb: number, cubeFt3: number): number {
  return weightLb / cubeFt3
}

const NMFC_BANDS: [number, number][] = [
  [50.0, 50], [35.0, 55], [22.5, 60], [15.0, 65],
  [13.5, 70], [12.0, 77.5], [10.5, 85], [9.0, 92.5],
  [8.0, 100], [7.0, 110], [6.0, 125], [5.0, 150],
  [4.0, 175], [3.0, 200], [2.0, 250], [1.0, 300],
  [0.5, 400],
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
  return (caseWeightLb / 100) * (gdsnRate - morRate)
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
