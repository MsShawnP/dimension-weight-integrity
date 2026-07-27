import { describe, it, expect } from 'vitest'
import { computeParadox } from './domain'

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
