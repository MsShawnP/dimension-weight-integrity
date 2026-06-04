import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import PortfolioView from './PortfolioView'
import type { AllSkusData } from '../types'

const HERO_SKU = {
  sku: 'CHP-0009',
  product_name: 'Cinderhaven Spicy Marinara (16 oz)',
  case_gross_weight_lb: 21.5,
  freight_class: 50,
  density_lb_per_ft3: 74.0,
  cost: {
    drivers: {
      ltl_reclass: { per_unit_delta: 0.39, annual_units: 52, annual_cost: 20.28 },
      parcel_reweigh: { per_unit_delta: 1.97, annual_units: 200, annual_cost: 394.0 },
      compliance_cb: { per_unit_delta: 200.0, annual_units: 3, annual_cost: 600.0 },
    },
    total_annual_cost: 1014.28,
  },
  divergence_count: 5,
}

const ZERO_COST_SKU = {
  sku: 'CHP-0050',
  product_name: 'Cinderhaven Classic Basil (8 oz)',
  case_gross_weight_lb: 12.0,
  freight_class: 50,
  density_lb_per_ft3: 80.0,
  cost: {
    drivers: {
      ltl_reclass: { per_unit_delta: 0, annual_units: 0, annual_cost: 0 },
      parcel_reweigh: { per_unit_delta: 0, annual_units: 0, annual_cost: 0 },
      compliance_cb: { per_unit_delta: 0, annual_units: 0, annual_cost: 0 },
    },
    total_annual_cost: 0,
  },
  divergence_count: 0,
}

const MEDIUM_COST_SKU = {
  sku: 'CHP-0025',
  product_name: 'Cinderhaven Garlic Aioli (12 oz)',
  case_gross_weight_lb: 18.0,
  freight_class: 55,
  density_lb_per_ft3: 60.0,
  cost: {
    drivers: {
      ltl_reclass: { per_unit_delta: 0.5, annual_units: 40, annual_cost: 20.0 },
      parcel_reweigh: { per_unit_delta: 0, annual_units: 0, annual_cost: 0 },
      compliance_cb: { per_unit_delta: 200.0, annual_units: 1, annual_cost: 200.0 },
    },
    total_annual_cost: 220.0,
  },
  divergence_count: 2,
}

function makeData(skus = [HERO_SKU, ZERO_COST_SKU, MEDIUM_COST_SKU]): AllSkusData {
  const total_annual_cost = skus.reduce((s, sk) => s + sk.cost.total_annual_cost, 0)
  const skus_with_class_mismatch = skus.filter(sk =>
    sk.cost.drivers.ltl_reclass.annual_cost > 0,
  ).length
  return {
    skus,
    aggregate: {
      total_annual_cost,
      skus_with_class_mismatch,
      total_skus: skus.length,
    },
  }
}

describe('PortfolioView', () => {
  it('renders the correct number of data rows', () => {
    const data = makeData()
    render(<PortfolioView data={data} />)
    const rows = screen.getAllByRole('row')
    // 1 header row + 3 data rows = 4
    expect(rows).toHaveLength(4)
  })

  it('shows aggregate KPIs: total cost, class mismatch count, total SKUs', () => {
    const data = makeData()
    render(<PortfolioView data={data} />)

    // Find each KPI card by its label, then check the value in the same card
    const costLabel = screen.getByText('Total annual cost of divergence')
    const costCard = costLabel.closest('.pv-kpi-card') as HTMLElement
    expect(within(costCard).getByText('$1,234.28')).toBeInTheDocument()

    const mismatchLabel = screen.getByText('SKUs with freight class mismatch')
    const mismatchCard = mismatchLabel.closest('.pv-kpi-card') as HTMLElement
    expect(within(mismatchCard).getByText('2')).toBeInTheDocument()

    const totalLabel = screen.getByText('Total SKUs analyzed')
    const totalCard = totalLabel.closest('.pv-kpi-card') as HTMLElement
    expect(within(totalCard).getByText('3')).toBeInTheDocument()
  })

  it('sorts by annual cost descending by default, toggles on header click', async () => {
    const user = userEvent.setup()
    const data = makeData()
    render(<PortfolioView data={data} />)

    const tbody = screen.getAllByRole('row').slice(1) // skip header
    // Default: desc by annual cost → hero ($1,014.28), medium ($220), zero ($0)
    expect(within(tbody[0]!).getByText('CHP-0009')).toBeInTheDocument()
    expect(within(tbody[1]!).getByText('CHP-0025')).toBeInTheDocument()
    expect(within(tbody[2]!).getByText('CHP-0050')).toBeInTheDocument()

    // Click Annual Cost header to toggle to ascending
    await user.click(screen.getByText(/Annual Cost/))
    const rowsAfter = screen.getAllByRole('row').slice(1)
    expect(within(rowsAfter[0]!).getByText('CHP-0050')).toBeInTheDocument()
    expect(within(rowsAfter[1]!).getByText('CHP-0025')).toBeInTheDocument()
    expect(within(rowsAfter[2]!).getByText('CHP-0009')).toBeInTheDocument()
  })

  it('expands a row on click to show per-driver cost detail', async () => {
    const user = userEvent.setup()
    const data = makeData()
    render(<PortfolioView data={data} />)

    // Driver details should not be visible initially
    expect(screen.queryByText('LTL Reclassification')).not.toBeInTheDocument()

    // Click the hero SKU row
    await user.click(screen.getByText('CHP-0009'))

    // Now driver detail is visible
    expect(screen.getByText('LTL Reclassification')).toBeInTheDocument()
    expect(screen.getByText('Parcel Reweigh')).toBeInTheDocument()
    expect(screen.getByText('Compliance Chargeback')).toBeInTheDocument()

    // Check per-unit and annual cost values
    expect(screen.getByText(/\$20\.28\/yr/)).toBeInTheDocument()
    expect(screen.getByText(/\$394\/yr/)).toBeInTheDocument()
    expect(screen.getByText(/\$600\/yr/)).toBeInTheDocument()

    // Click again to collapse
    await user.click(screen.getByText('CHP-0009'))
    expect(screen.queryByText('LTL Reclassification')).not.toBeInTheDocument()
  })

  it('hero SKU row shows matching cost data ($1,014.28)', () => {
    const data = makeData()
    render(<PortfolioView data={data} />)
    const heroRow = screen.getByText('CHP-0009').closest('tr')!
    expect(within(heroRow).getByText('$1,014.28')).toBeInTheDocument()
  })

  it('SKU with zero total cost shows $0', () => {
    const data = makeData()
    render(<PortfolioView data={data} />)
    const zeroRow = screen.getByText('CHP-0050').closest('tr')!
    expect(within(zeroRow).getByText('$0')).toBeInTheDocument()
  })
})
