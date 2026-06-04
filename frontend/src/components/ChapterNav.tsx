import type { Chapter } from '../types'
import { CHAPTER_ORDER } from '../types'

const CHAPTERS: { key: Chapter; label: string }[] = [
  { key: 'quiz', label: 'The Quiz' },
  { key: 'cost', label: 'The Cost' },
  { key: 'paradox', label: 'The Paradox' },
  { key: 'resolution', label: 'The Resolution' },
  { key: 'portfolio', label: 'The Portfolio' },
]

interface ChapterNavProps {
  active: Chapter
  furthest: Chapter
  onNavigate: (chapter: Chapter) => void
}

function chapterIndex(ch: Chapter): number {
  return CHAPTER_ORDER.indexOf(ch)
}

export default function ChapterNav({ active, furthest, onNavigate }: ChapterNavProps) {
  return (
    <nav className="chapter-nav" aria-label="Story chapters">
      {CHAPTERS.map((ch) => {
        const unlocked = chapterIndex(ch.key) <= chapterIndex(furthest)
        const isCurrent = ch.key === active

        return (
          <button
            key={ch.key}
            className={`chapter-tab ${isCurrent ? 'active' : ''} ${!unlocked ? 'locked' : ''}`}
            onClick={() => unlocked && onNavigate(ch.key)}
            disabled={!unlocked}
            aria-current={isCurrent ? 'step' : undefined}
          >
            {ch.label}
          </button>
        )
      })}
    </nav>
  )
}
