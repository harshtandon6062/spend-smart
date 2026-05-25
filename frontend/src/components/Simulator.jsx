import { useState, useCallback } from 'react';
import { simulate } from '../services/api';
import { formatCurrency } from '../utils/formatters';

export default function Simulator({ categories }) {
  const [reductions, setReductions] = useState(
    Object.fromEntries(categories.map((c) => [c.category, 0]))
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const debounceRef = {};

  const handleSliderChange = (category, value) => {
    const newReductions = { ...reductions, [category]: Number(value) };
    setReductions(newReductions);

    // Debounce API call
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await simulate(newReductions);
        setResult(res);
      } catch (err) {
        console.error('Simulation error:', err);
      } finally {
        setLoading(false);
      }
    }, 300);
  };

  return (
    <div className="simulator-grid">
      {/* Sliders */}
      <div className="card">
        <h3 style={{ marginBottom: '1.5rem', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
          Adjust spending reduction per category
        </h3>
        {categories.map((cat) => (
          <div className="slider-group" key={cat.category}>
            <label>
              {cat.category} ({formatCurrency(cat.total)})
              <span>{reductions[cat.category]}% cut</span>
            </label>
            <input
              type="range"
              min="0"
              max="50"
              value={reductions[cat.category]}
              onChange={(e) => handleSliderChange(cat.category, e.target.value)}
            />
          </div>
        ))}
      </div>

      {/* Results */}
      <div className="card">
        <div className="sim-summary">
          <div className="sim-label">Projected Monthly Savings</div>
          <div className="sim-amount">
            {result ? formatCurrency(result.total_savings) : '₹0'}
          </div>
          <div className="sim-label" style={{ marginTop: '0.5rem' }}>
            {result
              ? `New monthly total: ${formatCurrency(result.projected_total)}`
              : 'Move the sliders to simulate'}
          </div>
        </div>

        {result && result.category_savings && (
          <div style={{ marginTop: '1.5rem' }}>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Savings Breakdown
            </h4>
            {Object.entries(result.category_savings)
              .filter(([, v]) => v > 0)
              .sort(([, a], [, b]) => b - a)
              .map(([cat, amount]) => (
                <div
                  key={cat}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '0.5rem 0',
                    borderBottom: '1px solid var(--border-card)',
                    fontSize: '0.85rem',
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)' }}>{cat}</span>
                  <span style={{ color: 'var(--accent-green)', fontWeight: 600 }}>
                    -{formatCurrency(amount)}
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
