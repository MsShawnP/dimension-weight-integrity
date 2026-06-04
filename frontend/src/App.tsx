import { useState } from 'react'
import type { Chapter } from './types'
import ChapterNav from './components/ChapterNav'

const CHAPTER_ORDER: Chapter[] = ['quiz', 'cost', 'paradox', 'resolution', 'portfolio']

function chapterIndex(ch: Chapter): number {
  return CHAPTER_ORDER.indexOf(ch)
}

export default function App() {
  const [active, setActive] = useState<Chapter>('quiz')
  const [furthest, setFurthest] = useState<Chapter>('quiz')

  function navigate(chapter: Chapter) {
    setActive(chapter)
    if (chapterIndex(chapter) > chapterIndex(furthest)) {
      setFurthest(chapter)
    }
  }

  function advance() {
    const idx = chapterIndex(active)
    const next = CHAPTER_ORDER[idx + 1]
    if (next) {
      navigate(next)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="brand-title">Dimension &amp; Weight Integrity</h1>
        <p className="brand-subtitle">Cinderhaven Foods</p>
      </header>
      <ChapterNav active={active} furthest={furthest} onNavigate={navigate} />
      <main className="chapter-content">
        <ChapterPlaceholder chapter={active} onAdvance={advance} />
      </main>
    </div>
  )
}

function ChapterPlaceholder({ chapter, onAdvance }: { chapter: Chapter; onAdvance: () => void }) {
  const titles: Record<Chapter, string> = {
    quiz: 'The Quiz',
    cost: 'The Cost',
    paradox: 'The Paradox',
    resolution: 'The Resolution',
    portfolio: 'The Portfolio',
  }

  return (
    <section className="placeholder-chapter">
      <h2>{titles[chapter]}</h2>
      <p className="placeholder-text">Chapter content will be implemented in subsequent units.</p>
      {chapter !== 'portfolio' && (
        <button className="btn-primary" onClick={onAdvance}>
          Continue
        </button>
      )}
    </section>
  )
}
