export interface ParadoxResult {
  ltlCost: number
  parcelCost: number
  cbCost: number
  ltlFixed: boolean
  parcelFixed: boolean
}

// The frontend displays cost values precomputed by the dbt pipeline; it does
// not recompute freight physics client-side. computeParadox only toggles which
// precomputed base costs a governance scenario zeroes out.
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
