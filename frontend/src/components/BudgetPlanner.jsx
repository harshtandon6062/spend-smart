import { useState } from 'react';
import { formatCurrency } from '../utils/formatters';

export default function BudgetPlanner({ categories }) {
  const [budgets, setBudgets] = useState(
    Object.fromEntries(categories.map((c) => [c.category, '']))
  );

  const handleBudgetChange = (category, value) => {
    setBudgets({ ...budgets, [category]: value });
  };

  const getStatus = (actual, budget) => {
    if (!budget || budget <= 0) return { pct: 0, color: 'green', text: 'Set a budget' };
    const pct = (actual / budget) * 100;
    if (pct <= 80) return { pct, color: 'green', text: `${pct.toFixed(0)}% used` };
    if (pct <= 100) return { pct, color: 'amber', text: `${pct.toFixed(0)}% used` };
    return { pct: 100, color: 'red', text: `Over by ${formatCurrency(actual - budget)}` };
  };

  const totalBudget = Object.values(budgets).reduce((s, v) => s + (Number(v) || 0), 0);
  const totalActual = categories.reduce((s, c) => s + c.total, 0);

  return (
    <div className="card">
      <div className="budget-grid">
        {/* Header */}
        <div className="budget-row" style={{ borderBottom: '2px solid var(--border-card)' }}>
          <span className="category-name" style={{ fontWeight: 700, color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Category</span>
          <span style={{ fontWeight: 700, color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'right' }}>Budget</span>
          <span style={{ fontWeight: 700, color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Progress</span>
          <span style={{ fontWeight: 700, color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'right' }}>Status</span>
        </div>

        {categories.map((cat) => {
          const budget = Number(budgets[cat.category]) || 0;
          const status = getStatus(cat.total, budget);
          return (
            <div className="budget-row" key={cat.category}>
              <span className="category-name">
                {cat.category}
                <br />
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Actual: {formatCurrency(cat.total)}
                </span>
              </span>
              <input
                type="number"
                placeholder="₹ Budget"
                value={budgets[cat.category]}
                onChange={(e) => handleBudgetChange(cat.category, e.target.value)}
              />
              <div className="progress-bar-container">
                <div
                  className={`progress-bar-fill ${status.color}`}
                  style={{ width: `${Math.min(status.pct, 100)}%` }}
                />
              </div>
              <span className={`status-text`} style={{
                color: status.color === 'green' ? 'var(--accent-green)' :
                       status.color === 'amber' ? 'var(--accent-amber)' : 'var(--accent-red)'
              }}>
                {status.text}
              </span>
            </div>
          );
        })}

        {/* Total row */}
        {totalBudget > 0 && (
          <div className="budget-row" style={{ borderTop: '2px solid var(--border-card)', borderBottom: 'none', paddingTop: '1rem' }}>
            <span className="category-name" style={{ fontWeight: 700 }}>Total</span>
            <span style={{ textAlign: 'right', fontWeight: 600, color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>
              {formatCurrency(totalBudget)}
            </span>
            <div />
            <span className="status-text" style={{
              color: totalActual <= totalBudget ? 'var(--accent-green)' : 'var(--accent-red)'
            }}>
              {totalActual <= totalBudget
                ? `Under by ${formatCurrency(totalBudget - totalActual)}`
                : `Over by ${formatCurrency(totalActual - totalBudget)}`}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
