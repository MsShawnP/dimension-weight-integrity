import { useState } from 'react'
import type { Chapter } from './types'
import { CHAPTER_ORDER } from './types'
import { heroData, allSkusData } from './data'
import ChapterNav from './components/ChapterNav'
import QuizView from './components/QuizView'
import CostReveal from './components/CostReveal'
import ParadoxToggle from './components/ParadoxToggle'
import GovernanceResolution from './components/GovernanceResolution'
import PortfolioView from './components/PortfolioView'

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
        <p className="app-lede">
          Case weights and dimensions disagree across four systems &mdash;
          NetSuite, the WMS, GDSN, and Shopify. The mismatches silently
          reclassify freight, trigger parcel back-bills, and draw retailer
          chargebacks: about <strong>$20,000 a year</strong> across this 50-SKU
          portfolio.
        </p>
      </header>
      <ChapterNav active={active} furthest={furthest} onNavigate={navigate} />
      <main className="chapter-content">
        {active === 'quiz' && <QuizView data={heroData} onComplete={advance} />}
        {active === 'cost' && <CostReveal data={heroData} onComplete={advance} />}
        {active === 'paradox' && <ParadoxToggle data={heroData} onComplete={advance} />}
        {active === 'resolution' && (
          <>
            <GovernanceResolution data={heroData} />
            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <button className="btn-primary" onClick={advance}>Continue</button>
            </div>
          </>
        )}
        {active === 'portfolio' && <PortfolioView data={allSkusData} />}
      </main>
      <footer className="site-disclosure">
        <p>
          Built on the Cinderhaven synthetic dataset — a modeled ~$25M specialty
          food portfolio. Data is synthetic; methodology and cost models are real.
        </p>
      </footer>
    </div>
  )
}
