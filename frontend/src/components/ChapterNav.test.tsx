import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import ChapterNav from './ChapterNav'

describe('ChapterNav', () => {
  it('renders all five chapter tabs', () => {
    render(<ChapterNav active="quiz" furthest="quiz" onNavigate={vi.fn()} />)
    expect(screen.getByText('The Quiz')).toBeInTheDocument()
    expect(screen.getByText('The Cost')).toBeInTheDocument()
    expect(screen.getByText('The Paradox')).toBeInTheDocument()
    expect(screen.getByText('The Resolution')).toBeInTheDocument()
    expect(screen.getByText('The Portfolio')).toBeInTheDocument()
  })

  it('marks the active chapter with aria-current', () => {
    render(<ChapterNav active="cost" furthest="cost" onNavigate={vi.fn()} />)
    expect(screen.getByText('The Cost')).toHaveAttribute('aria-current', 'step')
    expect(screen.getByText('The Quiz')).not.toHaveAttribute('aria-current')
  })

  it('disables chapters beyond furthest', () => {
    render(<ChapterNav active="quiz" furthest="cost" onNavigate={vi.fn()} />)
    expect(screen.getByText('The Quiz')).not.toBeDisabled()
    expect(screen.getByText('The Cost')).not.toBeDisabled()
    expect(screen.getByText('The Paradox')).toBeDisabled()
    expect(screen.getByText('The Resolution')).toBeDisabled()
    expect(screen.getByText('The Portfolio')).toBeDisabled()
  })

  it('calls onNavigate when clicking an unlocked chapter', async () => {
    const onNavigate = vi.fn()
    render(<ChapterNav active="quiz" furthest="cost" onNavigate={onNavigate} />)
    await userEvent.click(screen.getByText('The Cost'))
    expect(onNavigate).toHaveBeenCalledWith('cost')
  })

  it('does not call onNavigate when clicking a locked chapter', async () => {
    const onNavigate = vi.fn()
    render(<ChapterNav active="quiz" furthest="quiz" onNavigate={vi.fn()} />)
    await userEvent.click(screen.getByText('The Paradox'))
    expect(onNavigate).not.toHaveBeenCalled()
  })
})
