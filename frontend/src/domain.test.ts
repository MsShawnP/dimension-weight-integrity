import { describe, it, expect } from 'vitest'
import {
  cubeFt3,
  densityLbPerFt3,
  densityToNmfcClass,
  dimWeightLb,
  billableWeightLb,
  computeLtlDelta,
  computeParcelDelta,
  computeParadox,
} from './domain'

describe('cubeFt3', () => {
  it('computes hero SKU cube', () => {
    expect(cubeFt3(11.25, 8.5, 5.25)).toBeCloseTo(0.29053, 4)
  })
})

describe('densityLbPerFt3', () => {
  it('computes hero SKU density', () => {
    const cube = cubeFt3(11.25, 8.5, 5.25)
    expect(densityLbPerFt3(21.5, cube)).toBeCloseTo(74.0, 0)
  })
})

describe('densityToNmfcClass', () => {
  it('returns class 50 for density >= 50', () => {
    expect(densityToNmfcClass(74.0)).toBe(50)
    expect(densityToNmfcClass(50.0)).toBe(50)
  })

  it('returns class 55 for density in [35, 50)', () => {
    expect(densityToNmfcClass(37.98)).toBe(55)
    expect(densityToNmfcClass(49.99)).toBe(55)
  })

  it('returns class 60 for density in [30, 35)', () => {
    // NMFC standard breakpoint the pre-fix table dropped entirely
    expect(densityToNmfcClass(30.0)).toBe(60)
    expect(densityToNmfcClass(34.99)).toBe(60)
  })

  it('returns class 65 for density in [22.5, 30)', () => {
    expect(densityToNmfcClass(22.5)).toBe(65)
    expect(densityToNmfcClass(29.99)).toBe(65)
  })

  it('returns class 70 for density in [15, 22.5)', () => {
    // NMFC standard: 15 pcf is class 70 (pre-fix table wrongly returned 65)
    expect(densityToNmfcClass(15.0)).toBe(70)
    expect(densityToNmfcClass(20.0)).toBe(70)
  })

  it('returns class 400 for density in [1, 2)', () => {
    expect(densityToNmfcClass(1.0)).toBe(400)
    expect(densityToNmfcClass(1.5)).toBe(400)
  })

  it('returns class 500 for density below 1', () => {
    // NMFC standard: below 1 pcf is class 500 (pre-fix table wrongly returned
    // 400 for [0.5, 1) via a spurious >=0.5 breakpoint)
    expect(densityToNmfcClass(0.7)).toBe(500)
    expect(densityToNmfcClass(0.3)).toBe(500)
  })
})

describe('dimWeightLb', () => {
  it('rounds each dimension up before computing', () => {
    expect(dimWeightLb(11.25, 8.5, 5.25, 139)).toBeCloseTo(
      (12 * 9 * 6) / 139,
      4,
    )
  })
})

describe('billableWeightLb', () => {
  it('returns the greater of actual and dim weight, ceiled', () => {
    expect(billableWeightLb(3.5, 4.66)).toBe(5)
    expect(billableWeightLb(10, 3)).toBe(10)
  })
})

describe('computeLtlDelta', () => {
  it('returns 0 when classes match', () => {
    const rates = { '50': 18.0, '55': 19.8 }
    expect(computeLtlDelta(50, 50, 21.5, rates)).toBe(0)
  })

  it('computes per-case delta when classes differ', () => {
    const rates = { '50': 18.0, '55': 19.8 }
    const delta = computeLtlDelta(55, 50, 21.5, rates)
    expect(delta).toBeCloseTo((21.5 / 100) * (19.8 - 18.0), 4)
  })

  it('floors a downward class shift at 0 (never a saving)', () => {
    const rates = { '50': 18.0, '55': 19.8 }
    // GDSN class 50 below MoR class 55 would imply a "saving", but a downward
    // reclass triggers a carrier reweigh/back-bill, so cost floors at 0.
    expect(computeLtlDelta(50, 55, 21.5, rates)).toBe(0)
  })
})

describe('computeParcelDelta', () => {
  const rates = { '1': 9.8, '2': 10.2, '3': 10.8, '4': 11.6, '5': 12.97 }

  it('returns the rate difference when billable exceeds shopify', () => {
    const delta = computeParcelDelta(5, 1, rates)
    expect(delta).toBeCloseTo(12.97 - 9.8, 4)
  })

  it('returns 0 when shopify weight is higher', () => {
    expect(computeParcelDelta(1, 5, rates)).toBe(0)
  })
})

describe('computeParadox', () => {
  const baseCosts = { ltl: 20.28, parcel: 394.0, cb: 600.0 }

  it('returns base costs when fixType is none', () => {
    const result = computeParadox('none', baseCosts)
    expect(result.ltlCost).toBe(20.28)
    expect(result.parcelCost).toBe(394.0)
    expect(result.ltlFixed).toBe(false)
    expect(result.parcelFixed).toBe(false)
  })

  it('zeroes LTL when ops fix applied', () => {
    const result = computeParadox('ops', baseCosts)
    expect(result.ltlCost).toBe(0)
    expect(result.ltlFixed).toBe(true)
    expect(result.parcelCost).toBe(394.0)
    expect(result.parcelFixed).toBe(false)
  })

  it('zeroes parcel when dtc fix applied', () => {
    const result = computeParadox('dtc', baseCosts)
    expect(result.parcelCost).toBe(0)
    expect(result.parcelFixed).toBe(true)
    expect(result.ltlCost).toBe(20.28)
    expect(result.ltlFixed).toBe(false)
  })
})
