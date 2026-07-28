import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import CostReveal from './CostReveal'
import heroJson from '../data/hero.json'
import { formatCurrency } from '../utils/format'
import type { HeroData } from '../types'

const data = heroJson as HeroData

// Derived from the shipped data, never frozen as literals. Hard-coded totals
// here previously outlived a defect in the pipeline: the suite stayed green
// while the LTL driver was priced against a pallet count instead of cases.
const ltl = data.cost.ltl_reclass!
const parcel = data.cost.parcel_reweigh!
const chargeback = data.cost.compliance_cb!
const total = Object.values(data.cost).reduce((s, d) => s + d.annual_cost, 0)

describe('CostReveal', () => {
  it('renders three cost driver sections with correct per-unit and annual amounts', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)

    for (const driver of [ltl, parcel, chargeback]) {
      const card = screen
        .getByText(`${formatCurrency(driver.annual_cost)}/yr`)
        .closest('section')!
      expect(card.textContent).toContain(formatCurrency(driver.per_unit_delta))
    }
  })

  it('shows class 50 vs class 55 comparison in LTL section', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    const ltlSection = screen.getByText('LTL Freight Reclassification').closest('section')!
    expect(ltlSection.textContent).toContain('class 55')
    expect(ltlSection.textContent).toContain('class 50')
  })

  it('shows Shopify weight and billable weight in parcel section', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    const parcelSection = screen.getByText('Parcel Reweigh Back-Billing').closest('section')!
    expect(parcelSection.textContent).toContain('1.00 lb')
    expect(parcelSection.textContent).toContain('3 lb')
  })

  it('shows the total annual cost as the sum of its drivers', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    expect(
      screen.getByText(`${formatCurrency(total)} per year`),
    ).toBeInTheDocument()
  })

  it('prices the LTL driver per case against an annual case volume', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    const ltlSection = screen
      .getByText('LTL Freight Reclassification')
      .closest('section')!
    // A pallet count would be a unit mismatch against a $/case delta.
    expect(ltlSection.textContent).toContain('cases/yr')
    expect(ltlSection.textContent).not.toContain('pallet')
    expect(ltl.annual_units).toBeGreaterThan(1000)
  })

  it('formats cost values correctly without trailing zeros beyond cents', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    // Whole-dollar amounts drop the cents; fractional amounts keep them.
    expect(formatCurrency(394)).toBe('$394')
    expect(formatCurrency(240)).toBe('$240')
    expect(formatCurrency(20.28)).toBe('$20.28')
    expect(screen.getByText(`${formatCurrency(parcel.annual_cost)}/yr`)).toBeInTheDocument()
    expect(screen.getByText(`${formatCurrency(chargeback.annual_cost)}/yr`)).toBeInTheDocument()
  })

  it('calls onComplete when Continue button is clicked', async () => {
    const onComplete = vi.fn()
    render(<CostReveal data={data} onComplete={onComplete} />)
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(onComplete).toHaveBeenCalledOnce()
  })
})
