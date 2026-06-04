import type { HeroData, AllSkusData } from './types'
import heroJson from './data/hero.json'
import allSkusJson from './data/all_skus.json'

export const heroData: HeroData = heroJson as unknown as HeroData
export const allSkusData: AllSkusData = allSkusJson as unknown as AllSkusData
