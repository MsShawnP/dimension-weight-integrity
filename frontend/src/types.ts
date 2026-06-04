export interface MeasurementOfRecord {
  source: string
  case_gross_weight_lb: number
  case_length_in: number
  case_width_in: number
  case_height_in: number
  case_cube_ft3: number
  density_lb_per_ft3: number
  freight_class: number
}

export interface SystemDivergence {
  field: string
  system_value: number
  mor_value: number
  abs_delta: number
  pct_delta: number
  flagged: boolean
}

export interface SystemData {
  system: string
  divergences: SystemDivergence[]
}

export interface FreightBySystem {
  density: number
  freight_class: number
}

export interface CostDriver {
  per_unit_delta: number
  annual_units: number
  annual_cost: number
  basis: Record<string, unknown>
}

export interface HeroSku {
  sku: string
  product_name: string
  measurement_of_record: MeasurementOfRecord
  systems: SystemData[]
  freight_by_system: Record<string, FreightBySystem>
}

export interface RateTables {
  ltl_rate_per_cwt: Record<string, number>
  parcel_rate_per_lb: Record<string, number>
  dim_divisor: number
}

export interface Paradox {
  ops_fix: { description: string; effect: string }
  dtc_fix: { description: string; effect: string }
}

export interface HeroData {
  hero_sku: HeroSku
  cost: Record<string, CostDriver>
  rate_tables: RateTables
  paradox: Paradox
}

export interface SkuCostDrivers {
  drivers: Record<string, { per_unit_delta: number; annual_units: number; annual_cost: number }>
  total_annual_cost: number
}

export interface SkuSummary {
  sku: string
  product_name: string
  case_gross_weight_lb: number
  freight_class: number
  density_lb_per_ft3: number
  cost: SkuCostDrivers
  divergence_count: number
}

export interface AllSkusData {
  skus: SkuSummary[]
  aggregate: {
    total_annual_cost: number
    skus_with_class_mismatch: number
    total_skus: number
  }
}

export type Chapter = 'quiz' | 'cost' | 'paradox' | 'resolution' | 'portfolio'

export const CHAPTER_ORDER: Chapter[] = ['quiz', 'cost', 'paradox', 'resolution', 'portfolio']
