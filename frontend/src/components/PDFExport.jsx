import { useState, useRef } from 'react';
import { LuFileDown } from 'react-icons/lu';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { formatCurrency, formatPercent, formatDateFull } from '../utils/formatters';

export default function PDFExport({ analytics, recommendations }) {
  const [exporting, setExporting] = useState(false);
  const reportRef = useRef(null);

  const handleExport = async () => {
    setExporting(true);
    try {
      const el = reportRef.current;
      if (!el) return;

      // Temporarily show the hidden report div
      el.style.display = 'block';

      const canvas = await html2canvas(el, {
        scale: 2,
        backgroundColor: '#0f1329',
        useCORS: true,
        logging: false,
        width: el.scrollWidth,
        height: el.scrollHeight,
      });

      el.style.display = 'none';

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      const pageHeight = pdf.internal.pageSize.getHeight();

      let position = 0;
      if (pdfHeight <= pageHeight) {
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      } else {
        while (position < pdfHeight) {
          pdf.addImage(imgData, 'PNG', 0, -position, pdfWidth, pdfHeight);
          position += pageHeight;
          if (position < pdfHeight) pdf.addPage();
        }
      }

      pdf.save('SpendSmart_Report.pdf');
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
      setExporting(false);
    }
  };

  if (!analytics) return null;

  const topCategory = analytics.category_totals[0];
  const topInsights = recommendations
    .filter((r) => r.priority === 'high' || r.priority === 'medium')
    .slice(0, 8);

  const totalPotential = Math.min(
    recommendations.reduce((max, r) => {
      return r.title.includes('save 20%') ? r.savings_estimate : max;
    }, 0) || analytics.total_spend * 0.15,
    analytics.total_spend * 0.3
  );

  return (
    <>
      <button
        className="btn-primary"
        onClick={handleExport}
        disabled={exporting}
        style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
      >
        <LuFileDown />
        {exporting ? 'Generating...' : 'Export PDF'}
      </button>

      {/* Hidden report layout — only rendered into the PDF */}
      <div
        ref={reportRef}
        style={{
          display: 'none',
          position: 'absolute',
          left: '-9999px',
          top: 0,
          width: '800px',
          fontFamily: 'Inter, sans-serif',
          color: '#f0f0f5',
          background: '#0f1329',
          padding: '40px',
        }}
      >
        {/* Header */}
        <div style={{
          textAlign: 'center',
          marginBottom: '32px',
          paddingBottom: '24px',
          borderBottom: '2px solid rgba(0,212,255,0.2)',
        }}>
          <h1 style={{
            fontSize: '28px',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #00d4ff, #7b2ff7)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '8px',
          }}>
            💰 SpendSmart Report
          </h1>
          <p style={{ color: '#8b8fa3', fontSize: '13px' }}>
            Spending Analysis &bull; {formatDateFull(analytics.date_range?.start)} — {formatDateFull(analytics.date_range?.end)}
          </p>
        </div>

        {/* Summary Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '12px',
          marginBottom: '32px',
        }}>
          {[
            { label: 'Total Spend', value: formatCurrency(analytics.total_spend), color: '#00d4ff' },
            { label: 'Daily Average', value: formatCurrency(analytics.daily_average), color: '#7b2ff7' },
            { label: 'Top Category', value: `${topCategory?.category} (${topCategory?.percentage}%)`, color: '#f72f8e' },
            { label: 'Potential Savings', value: formatCurrency(totalPotential), color: '#00e68a' },
          ].map((stat, i) => (
            <div key={i} style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '12px',
              padding: '16px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '11px', color: '#8b8fa3', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                {stat.label}
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: stat.color }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Category Breakdown Table */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px', color: '#00d4ff' }}>
            📊 Category Breakdown
          </h2>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(255,255,255,0.1)' }}>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: '#8b8fa3', fontWeight: 600 }}>Category</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b8fa3', fontWeight: 600 }}>Amount</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b8fa3', fontWeight: 600 }}>Share</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b8fa3', fontWeight: 600 }}>Txns</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: '#8b8fa3', fontWeight: 600 }}>Bar</th>
              </tr>
            </thead>
            <tbody>
              {analytics.category_totals.map((cat, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 500 }}>{cat.category}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>{formatCurrency(cat.total)}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>{formatPercent(cat.percentage)}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', color: '#8b8fa3' }}>{cat.count}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <div style={{
                      width: '120px', height: '8px',
                      background: 'rgba(255,255,255,0.06)',
                      borderRadius: '4px', overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${cat.percentage}%`, height: '100%',
                        background: ['#00d4ff', '#7b2ff7', '#f72f8e', '#00e68a', '#ffb347', '#ff4757', '#5f6fff'][i % 7],
                        borderRadius: '4px',
                      }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Top Merchants */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px', color: '#00d4ff' }}>
            🏪 Top Merchants
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
            {analytics.top_merchants.map((m, i) => (
              <div key={i} style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '10px',
                padding: '12px',
                textAlign: 'center',
              }}>
                <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>{m.merchant}</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#00d4ff' }}>{formatCurrency(m.total)}</div>
                <div style={{ fontSize: '11px', color: '#8b8fa3' }}>{m.count} visits</div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekday vs Weekend */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px', color: '#00d4ff' }}>
            📅 Weekday vs Weekend
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{
              background: 'rgba(0,212,255,0.06)',
              border: '1px solid rgba(0,212,255,0.15)',
              borderRadius: '10px', padding: '16px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '11px', color: '#8b8fa3', textTransform: 'uppercase', marginBottom: '4px' }}>Weekday Avg/Day</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#00d4ff' }}>
                {formatCurrency(analytics.weekday_vs_weekend.weekday_avg)}
              </div>
            </div>
            <div style={{
              background: 'rgba(247,47,142,0.06)',
              border: '1px solid rgba(247,47,142,0.15)',
              borderRadius: '10px', padding: '16px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '11px', color: '#8b8fa3', textTransform: 'uppercase', marginBottom: '4px' }}>Weekend Avg/Day</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#f72f8e' }}>
                {formatCurrency(analytics.weekday_vs_weekend.weekend_avg)}
              </div>
            </div>
          </div>
        </div>

        {/* Top Insights */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px', color: '#00d4ff' }}>
            💡 Key Insights & Recommendations
          </h2>
          {topInsights.map((rec, i) => {
            const borderColor = rec.priority === 'high' ? '#ff4757' : '#ffb347';
            return (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                padding: '12px',
                marginBottom: '8px',
                background: 'rgba(255,255,255,0.03)',
                borderLeft: `3px solid ${borderColor}`,
                borderRadius: '8px',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '3px' }}>{rec.title}</div>
                  <div style={{ fontSize: '11px', color: '#8b8fa3', lineHeight: 1.5 }}>{rec.description}</div>
                </div>
                {rec.savings_estimate > 0 && (
                  <div style={{
                    flexShrink: 0, padding: '4px 10px',
                    borderRadius: '16px', fontSize: '12px', fontWeight: 600,
                    background: 'rgba(0,230,138,0.1)', color: '#00e68a',
                    whiteSpace: 'nowrap',
                  }}>
                    Save {formatCurrency(rec.savings_estimate)}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          paddingTop: '16px',
          borderTop: '1px solid rgba(255,255,255,0.08)',
          fontSize: '11px',
          color: '#5a5e73',
        }}>
          Generated by SpendSmart • {new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
        </div>
      </div>
    </>
  );
}
