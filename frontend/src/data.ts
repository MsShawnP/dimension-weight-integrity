import type { HeroData, AllSkusData } from './types'
import heroJson from './data/hero.json'
import allSkusJson from './data/all_skus.json'

// These guards run at import time. They check the shapes the components
// actually index into — not just the top-level keys — so a malformed export
// fails loudly here instead of rendering "undefined" somewhere downstream.
function assertHeroData(data: unknown): asserts data is HeroData {
  const obj = data as Record<string, unknown>
  if (!obj.hero_sku || !obj.cost || !obj.paradox) {
    throw new Error('hero.json missing required keys: hero_sku, cost, paradox')
  }
  const hero = obj.hero_sku as Record<string, unknown>
  if (!Array.isArray(hero.systems)) {
    throw new Error('hero.json: hero_sku.systems must be an array')
  }
  if (!hero.measurement_of_record) {
    throw new Error('hero.json: hero_sku.measurement_of_record is missing')
  }
  for (const system of hero.systems as Record<string, unknown>[]) {
    if (!Array.isArray(system.divergences)) {
      throw new Error(`hero.json: systems[${String(system.system)}].divergences must be an array`)
    }
  }
  // ParadoxToggle and GovernanceResolution read these three drivers by name.
  for (const driver of ['ltl_reclass', 'parcel_reweigh', 'compliance_cb']) {
    const entry = (obj.cost as Record<string, unknown>)[driver] as Record<string, unknown> | undefined
    if (!entry || typeof entry.annual_cost !== 'number') {
      throw new Error(`hero.json: cost.${driver}.annual_cost must be a number`)
    }
  }
}

function assertAllSkusData(data: unknown): asserts data is AllSkusData {
  const obj = data as Record<string, unknown>
  if (!Array.isArray(obj.skus) || !obj.aggregate) {
    throw new Error('all_skus.json missing required keys: skus, aggregate')
  }
  const aggregate = obj.aggregate as Record<string, unknown>
  // The hero headline renders aggregate.total_annual_cost directly.
  for (const field of ['total_annual_cost', 'skus_with_class_mismatch', 'total_skus']) {
    if (typeof aggregate[field] !== 'number') {
      throw new Error(`all_skus.json: aggregate.${field} must be a number`)
    }
  }
  for (const sku of obj.skus as Record<string, unknown>[]) {
    const cost = sku.cost as Record<string, unknown> | undefined
    if (!cost || typeof cost.total_annual_cost !== 'number' || !cost.drivers) {
      throw new Error(`all_skus.json: ${String(sku.sku)} has a malformed cost block`)
    }
  }
}

assertHeroData(heroJson)
assertAllSkusData(allSkusJson)

export const heroData: HeroData = heroJson
export const allSkusData: AllSkusData = allSkusJson
