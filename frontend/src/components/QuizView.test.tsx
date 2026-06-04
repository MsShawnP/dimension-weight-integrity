import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import QuizView from './QuizView'
import heroJson from '../data/hero.json'
import type { HeroData } from '../types'

const data = heroJson as HeroData

describe('QuizView', () => {
  it('marks ERP as selected and reveals it as wrong', async () => {
    const onComplete = vi.fn()
    render(<QuizView data={data} onComplete={onComplete} />)

    await userEvent.click(screen.getByText('NetSuite ERP'))
    expect(screen.getByText('NetSuite ERP').closest('button')).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    await userEvent.click(screen.getByRole('button', { name: /reveal/i }))
    expect(
      screen.getByText('Net weight stored in gross field — biased low'),
    ).toBeInTheDocument()
  })

  it('shows WMS as correct when selected and revealed', async () => {
    const onComplete = vi.fn()
    render(<QuizView data={data} onComplete={onComplete} />)

    await userEvent.click(screen.getByText('3PL / WMS'))
    await userEvent.click(screen.getByRole('button', { name: /reveal/i }))

    const wmsCard = screen.getByText('3PL / WMS').closest('button')!
    expect(wmsCard.className).toContain('quiz-card--correct')
    expect(
      screen.getByText(
        'Physical measurement at receiving — the measurement of record',
      ),
    ).toBeInTheDocument()
  })

  it('does not show Reveal button before any selection', () => {
    render(<QuizView data={data} onComplete={vi.fn()} />)
    const revealBtn = screen.getByRole('button', { name: /reveal/i })
    expect(revealBtn).toBeDisabled()
  })

  it('shows all four annotations after reveal', async () => {
    render(<QuizView data={data} onComplete={vi.fn()} />)

    await userEvent.click(screen.getByText('NetSuite ERP'))
    await userEvent.click(screen.getByRole('button', { name: /reveal/i }))

    expect(
      screen.getByText('Net weight stored in gross field — biased low'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Physical measurement at receiving — the measurement of record',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Outer-box dims inflated for safe transit — overstates density',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Unit net weight, not case gross — wildly understated'),
    ).toBeInTheDocument()
  })

  it('changes selection when clicking a different card before reveal', async () => {
    render(<QuizView data={data} onComplete={vi.fn()} />)

    await userEvent.click(screen.getByText('NetSuite ERP'))
    expect(screen.getByText('NetSuite ERP').closest('button')).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    await userEvent.click(screen.getByText('GDSN (IX-ONE)'))
    expect(
      screen.getByText('GDSN (IX-ONE)').closest('button'),
    ).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('NetSuite ERP').closest('button')).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })

  it('locks cards after reveal — clicking does not change state', async () => {
    render(<QuizView data={data} onComplete={vi.fn()} />)

    await userEvent.click(screen.getByText('3PL / WMS'))
    await userEvent.click(screen.getByRole('button', { name: /reveal/i }))

    // All cards should be disabled
    const cards = screen
      .getAllByRole('button')
      .filter((b) => b.className.includes('quiz-card'))
    for (const card of cards) {
      expect(card).toBeDisabled()
    }
  })
})
