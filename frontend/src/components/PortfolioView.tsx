import { useState } from 'react'
import type { AllSkusData, SkuSummary } from '../types'
import { formatCurrency, formatWeight, formatClass } from '../utils/format'

interface PortfolioViewProps {
  data: AllSkusData
}

type SortColumn = 'sku' | 'product_name' | 'case_gross_weight_lb' | 'freight_class' | 'divergence_count' | 'annual_cost'
type SortDirection = 'asc' | 'desc'

const DRIVER_LABELS: Record<string, string> = {
  ltl_reclass: 'LTL Reclassification',
  parcel_reweigh: 'Parcel Reweigh',
  compliance_cb: 'Compliance Chargeback',
}

function getSortValue(sku: SkuSummary, column: SortColumn): string | number {
  switch (column) {
    case 'sku': return sku.sku
    case 'product_name': return sku.product_name
    case 'case_gross_weight_lb': return sku.case_gross_weight_lb
    case 'freight_class': return sku.freight_class
    case 'divergence_count': return sku.divergence_count
    case 'annual_cost': return sku.cost.total_annual_cost
  }
}

function sortSkus(skus: SkuSummary[], column: SortColumn, direction: SortDirection): SkuSummary[] {
  return [...skus].sort((a, b) => {
    const aVal = getSortValue(a, column)
    const bVal = getSortValue(b, column)
    const cmp = typeof aVal === 'string' && typeof bVal === 'string'
      ? aVal.localeCompare(bVal)
      : (aVal as number) - (bVal as number)
    return direction === 'asc' ? cmp : -cmp
  })
}

function SortArrow({ column, sortColumn, sortDirection }: { column: SortColumn; sortColumn: SortColumn; sortDirection: SortDirection }) {
  if (column !== sortColumn) return null
  return <span className="pv-sort-arrow" aria-hidden="true">{sortDirection === 'asc' ? ' ▲' : ' ▼'}</span>
}

export default function PortfolioView({ data }: PortfolioViewProps) {
  const [sortColumn, setSortColumn] = useState<SortColumn>('annual_cost')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [expandedSku, setExpandedSku] = useState<string | null>(null)

  const handleSort = (column: SortColumn) => {
    if (column === sortColumn) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('desc')
    }
  }

  const handleRowClick = (sku: string) => {
    setExpandedSku(prev => prev === sku ? null : sku)
  }

  const sorted = sortSkus(data.skus, sortColumn, sortDirection)

  return (
    <div className="pv">
      <div className="pv-kpis">
        <div className="pv-kpi-card">
          <span className="pv-kpi-value">{formatCurrency(data.aggregate.total_annual_cost)}</span>
          <span className="pv-kpi-label">Total annual cost of divergence</span>
        </div>
        <div className="pv-kpi-card">
          <span className="pv-kpi-value">{data.aggregate.skus_with_class_mismatch}</span>
          <span className="pv-kpi-label">SKUs with freight class mismatch</span>
        </div>
        <div className="pv-kpi-card">
          <span className="pv-kpi-value">{data.aggregate.total_skus}</span>
          <span className="pv-kpi-label">Total SKUs analyzed</span>
        </div>
      </div>

      <div className="pv-table-wrapper">
        <table className="pv-table">
          <thead>
            <tr>
              <th className="pv-th" onClick={() => handleSort('sku')}>
                SKU<SortArrow column="sku" sortColumn={sortColumn} sortDirection={sortDirection} />
              </th>
              <th className="pv-th" onClick={() => handleSort('product_name')}>
                Product Name<SortArrow column="product_name" sortColumn={sortColumn} sortDirection={sortDirection} />
              </th>
              <th className="pv-th" onClick={() => handleSort('case_gross_weight_lb')}>
                MoR Weight (lb)<SortArrow column="case_gross_weight_lb" sortColumn={sortColumn} sortDirection={sortDirection} />
              </th>
              <th className="pv-th" onClick={() => handleSort('freight_class')}>
                Freight Class<SortArrow column="freight_class" sortColumn={sortColumn} sortDirection={sortDirection} />
              </th>
              <th className="pv-th" onClick={() => handleSort('divergence_count')}>
                Divergence Count<SortArrow column="divergence_count" sortColumn={sortColumn} sortDirection={sortDirection} />
              </th>
              <th className="pv-th pv-th--right" onClick={() => handleSort('annual_cost')}>
                Annual Cost<SortArrow column="annual_cost" sortColumn={sortColumn} sortDirection={sortDirection} />
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(sku => (
              <SkuRow
                key={sku.sku}
                sku={sku}
                isExpanded={expandedSku === sku.sku}
                onToggle={() => handleRowClick(sku.sku)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function SkuRow({ sku, isExpanded, onToggle }: { sku: SkuSummary; isExpanded: boolean; onToggle: () => void }) {
  // Show every driver that contributes to the row total (nonzero) so the
  // expanded breakdown always reconciles to the total shown in the row. A
  // negative driver (should one ever appear) is displayed, not hidden while
  // still counting toward the total.
  const activeDrivers = Object.entries(sku.cost.drivers).filter(
    ([, d]) => d.annual_cost !== 0,
  )

  return (
    <>
      <tr className="pv-row" onClick={onToggle} style={{ cursor: 'pointer' }}>
        <td className="pv-td">{sku.sku}</td>
        <td className="pv-td">{sku.product_name}</td>
        <td className="pv-td">{formatWeight(sku.case_gross_weight_lb)}</td>
        <td className="pv-td">{formatClass(sku.freight_class)}</td>
        <td className="pv-td">{sku.divergence_count}</td>
        <td className="pv-td pv-td--right">{formatCurrency(sku.cost.total_annual_cost)}</td>
      </tr>
      {isExpanded && (
        <tr className="pv-expanded-row">
          <td className="pv-expanded-cell" colSpan={6}>
            <div className="pv-expanded-panel">
              <h4 className="pv-expanded-title">Cost Drivers</h4>
              {activeDrivers.length === 0 && (
                <p className="pv-expanded-none">No active cost drivers.</p>
              )}
              {activeDrivers.map(([key, driver]) => (
                <div key={key} className="pv-driver-row">
                  <span className="pv-driver-name">{DRIVER_LABELS[key] ?? key}</span>
                  <span className="pv-driver-detail">
                    {formatCurrency(driver.per_unit_delta)}/unit &times; {driver.annual_units} units
                  </span>
                  <span className="pv-driver-cost">{formatCurrency(driver.annual_cost)}/yr</span>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
