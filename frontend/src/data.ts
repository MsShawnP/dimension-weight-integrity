import type { HeroData, AllSkusData } from './types'
import heroJson from './data/hero.json'
import allSkusJson from './data/all_skus.json'

function assertHeroData(data: unknown): asserts data is HeroData {
  const obj = data as Record<string, unknown>
  if (!obj.hero_sku || !obj.cost || !obj.rate_tables || !obj.paradox) {
    throw new Error('hero.json missing required keys: hero_sku, cost, rate_tables, paradox')
  }
}

function assertAllSkusData(data: unknown): asserts data is AllSkusData {
  const obj = data as Record<string, unknown>
  if (!Array.isArray(obj.skus) || !obj.aggregate) {
    throw new Error('all_skus.json missing required keys: skus, aggregate')
  }
}

assertHeroData(heroJson)
assertAllSkusData(allSkusJson)

export const heroData: HeroData = heroJson
export const allSkusData: AllSkusData = allSkusJson
