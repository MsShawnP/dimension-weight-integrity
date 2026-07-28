import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import ParadoxToggle from './ParadoxToggle'
import GovernanceResolution from './GovernanceResolution'
import heroJson from '../data/hero.json'
import { formatCurrency } from '../utils/format'
import type { HeroData } from '../types'

const data = heroJson as HeroData

// Derived from the shipped data, never frozen as literals. Hard-coded cost
// constants here previously outlived a defect in the pipeline: the suite
// stayed green while the LTL driver was priced against a pallet count.
const money = (v: number) => formatCurrency(v)
const ltlCost = money(data.cost.ltl_reclass!.annual_cost)
const parcelCost = money(data.cost.parcel_reweigh!.annual_cost)
const chargebackCost = money(data.cost.compliance_cb!.annual_cost)

describe('ParadoxToggle', () => {
  it('shows base costs for both channels in Current State', () => {
    render(<ParadoxToggle data={data} onComplete={vi.fn()} />)

    // Both channels should show "Unresolved"
    const statuses = screen.getAllByText('Unresolved')
    expect(statuses).toHaveLength(2)

    // Each driver's shipped annual cost should be on screen
    expect(screen.getByText(ltlCost)).toBeInTheDocument()
    expect(screen.getByText(parcelCost)).toBeInTheDocument()
    expect(screen.getByText(chargebackCost)).toBeInTheDocument()
  })

  it('Fix Retail (Ops) clears retail channel, parcel remains', async () => {
    render(<ParadoxToggle data={data} onComplete={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: 'Fix Retail (Ops)' }))

    // Retail channel should be fixed
    expect(screen.getByText('Fixed')).toBeInTheDocument()
    // Parcel channel should still be unresolved
    expect(screen.getByText('Unresolved')).toBeInTheDocument()

    // LTL cost and chargebacks should be $0
    const zeros = screen.getAllByText('$0')
    expect(zeros.length).toBeGreaterThanOrEqual(2)

    // Parcel cost should remain (in channel card and summary)
    expect(screen.getAllByText(parcelCost).length).toBeGreaterThanOrEqual(1)
  })

  it('Fix DTC clears parcel channel, retail remains', async () => {
    render(<ParadoxToggle data={data} onComplete={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: 'Fix DTC' }))

    // Parcel channel should be fixed
    expect(screen.getByText('Fixed')).toBeInTheDocument()
    // Retail channel should still be unresolved
    expect(screen.getByText('Unresolved')).toBeInTheDocument()

    // Parcel cost should be $0
    expect(screen.getAllByText('$0')).toHaveLength(1)

    // LTL cost and chargebacks should remain
    expect(screen.getByText(ltlCost)).toBeInTheDocument()
    expect(screen.getByText(chargebackCost)).toBeInTheDocument()
  })

  it('no toggle state shows both channels as Fixed simultaneously', async () => {
    render(<ParadoxToggle data={data} onComplete={vi.fn()} />)

    // Current State: both unresolved
    expect(screen.queryAllByText('Fixed')).toHaveLength(0)
    expect(screen.getAllByText('Unresolved')).toHaveLength(2)

    // Fix Retail (Ops): one fixed, one unresolved
    await userEvent.click(screen.getByRole('button', { name: 'Fix Retail (Ops)' }))
    expect(screen.getAllByText('Fixed')).toHaveLength(1)
    expect(screen.getAllByText('Unresolved')).toHaveLength(1)

    // Fix DTC: one fixed, one unresolved
    await userEvent.click(screen.getByRole('button', { name: 'Fix DTC' }))
    expect(screen.getAllByText('Fixed')).toHaveLength(1)
    expect(screen.getAllByText('Unresolved')).toHaveLength(1)

    // Back to current state: both unresolved
    await userEvent.click(screen.getByRole('button', { name: 'Current State' }))
    expect(screen.queryAllByText('Fixed')).toHaveLength(0)
    expect(screen.getAllByText('Unresolved')).toHaveLength(2)
  })

  it('rapid toggling between states produces correct values', async () => {
    render(<ParadoxToggle data={data} onComplete={vi.fn()} />)
    const user = userEvent.setup()

    const opsBtn = screen.getByRole('button', { name: 'Fix Retail (Ops)' })
    const dtcBtn = screen.getByRole('button', { name: 'Fix DTC' })
    const currentBtn = screen.getByRole('button', { name: 'Current State' })

    // Rapid cycle: ops → dtc → current → ops → dtc
    await user.click(opsBtn)
    await user.click(dtcBtn)
    await user.click(currentBtn)
    await user.click(opsBtn)
    await user.click(dtcBtn)

    // Should settle on DTC fix state
    expect(screen.getByText('Fixed')).toBeInTheDocument()
    expect(screen.getByText('Unresolved')).toBeInTheDocument()
    expect(screen.getByText(ltlCost)).toBeInTheDocument()
    expect(screen.getByText(chargebackCost)).toBeInTheDocument()
    expect(screen.getAllByText('$0')).toHaveLength(1)
  })
})

describe('GovernanceResolution', () => {
  it('renders with both channels showing as resolved', () => {
    render(<GovernanceResolution data={data} />)

    // Both channels should show "Fixed"
    const fixedStatuses = screen.getAllByText('Fixed')
    expect(fixedStatuses).toHaveLength(2)

    // No "Unresolved" should appear
    expect(screen.queryByText('Unresolved')).not.toBeInTheDocument()

    // All costs should be $0
    const zeros = screen.getAllByText('$0')
    expect(zeros.length).toBeGreaterThanOrEqual(3)

    // Title should be present
    expect(
      screen.getByText('The Resolution: Governed Measurement of Record'),
    ).toBeInTheDocument()

    // Key insight should be present
    expect(
      screen.getByText(/governed measurement of record is the only configuration/i),
    ).toBeInTheDocument()
  })
})
