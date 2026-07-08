import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import CostReveal from './CostReveal'
import heroJson from '../data/hero.json'
import type { HeroData } from '../types'

const data = heroJson as HeroData

describe('CostReveal', () => {
  it('renders three cost driver sections with correct per-unit and annual amounts', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)

    // LTL: $0.39/case, $20.28/yr
    expect(screen.getByText(/\$0\.39/)).toBeInTheDocument()
    expect(screen.getByText(/\$20\.28\/yr/)).toBeInTheDocument()

    // Parcel: $1.97/shipment, $394/yr
    expect(screen.getByText(/\$1\.97/)).toBeInTheDocument()
    expect(screen.getByText(/\$394\/yr/)).toBeInTheDocument()

    // Compliance: $200/event, risk-adjusted to 1.2 expected events/yr → $240/yr
    expect(screen.getByText(/\$200/)).toBeInTheDocument()
    expect(screen.getByText(/\$240\/yr/)).toBeInTheDocument()
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

  it('shows total annual cost of $654.28', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    expect(screen.getByText(/\$654\.28/)).toBeInTheDocument()
  })

  it('formats cost values correctly without trailing zeros beyond cents', () => {
    render(<CostReveal data={data} onComplete={vi.fn()} />)
    // $394 not $394.00, $240 not $240.00, $200 not $200.00
    expect(screen.getByText(/\$394\/yr/)).toBeInTheDocument()
    expect(screen.getByText(/\$240\/yr/)).toBeInTheDocument()
    // $20.28 keeps its cents, $0.39 keeps its cents
    expect(screen.getByText(/\$20\.28\/yr/)).toBeInTheDocument()
    expect(screen.getByText(/\$0\.39/)).toBeInTheDocument()
  })

  it('calls onComplete when Continue button is clicked', async () => {
    const onComplete = vi.fn()
    render(<CostReveal data={data} onComplete={onComplete} />)
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(onComplete).toHaveBeenCalledOnce()
  })
})
