import { useState, useRef } from 'react';
import { LuFileDown, LuSparkles } from 'react-icons/lu';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { formatCurrency, formatPercent, formatDateFull } from '../utils/formatters';
import { getAIReport } from '../services/api';

export default function PDFExport({ analytics, recommendations }) {
  const [exporting, setExporting] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const reportRef = useRef(null);
  const aiReportRef = useRef(null);

  // ─── Regular Report Export ───────────────────────────────
  const handleExport = async () => {
    setExporting(true);
    try {
      const el = reportRef.current;
      if (!el) return;

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

  // ─── AI Report Export ────────────────────────────────────
  const handleAIExport = async () => {
    setAiLoading(true);
    try {
      const { report } = await getAIReport();
      await renderAIReport(report);
    } catch (err) {
      console.error('AI report failed:', err);
      alert('AI report generation failed. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const renderAIReport = async (markdown) => {
    const el = aiReportRef.current;
    if (!el) return;

    // Convert markdown to styled HTML
    el.innerHTML = buildAIReportHTML(markdown);
    el.style.display = 'block';

    // Wait for fonts/rendering
    await new Promise(r => setTimeout(r, 300));

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

    pdf.save('SpendSmart_AI_Report.pdf');
  };

  const buildAIReportHTML = (markdown) => {
    // Simple markdown → HTML conversion for the report
    let html = markdown
      // Headers
      .replace(/^### (.*$)/gm, '<h3 style="font-size:15px;font-weight:700;color:#7b2ff7;margin:16px 0 8px;">$1</h3>')
      .replace(/^## (.*$)/gm, '<h2 style="font-size:18px;font-weight:700;color:#00d4ff;margin:24px 0 10px;padding-bottom:6px;border-bottom:1px solid rgba(0,212,255,0.15);">$1</h2>')
      .replace(/^# (.*$)/gm, '<h1 style="font-size:24px;font-weight:800;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;">$1</h1>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#f0f0f5;font-weight:600;">$1</strong>')
      // Bullets
      .replace(/^- (.*$)/gm, '<div style="display:flex;gap:8px;margin:4px 0 4px 12px;"><span style="color:#00d4ff;flex-shrink:0;">•</span><span>$1</span></div>')
      // Numbered lists
      .replace(/^(\d+)\. (.*$)/gm, '<div style="display:flex;gap:8px;margin:6px 0 6px 12px;"><span style="color:#00e68a;font-weight:700;flex-shrink:0;">$1.</span><span>$2</span></div>')
      // Paragraphs (double newline)
      .replace(/\n\n/g, '</p><p style="margin:8px 0;line-height:1.7;color:#c0c4d6;">')
      // Single newlines (after list processing)
      .replace(/\n/g, '<br/>');

    return `
      <div style="text-align:center;margin-bottom:28px;padding-bottom:20px;border-bottom:2px solid rgba(0,212,255,0.2);">
        <h1 style="font-size:28px;font-weight:800;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;">
          🤖 SpendSmart AI Report
        </h1>
        <p style="color:#8b8fa3;font-size:13px;">
          AI-Powered Financial Analysis • ${formatDateFull(analytics.date_range?.start)} — ${formatDateFull(analytics.date_range?.end)}
        </p>
        <p style="color:#5a5e73;font-size:11px;margin-top:4px;">
          Powered by Llama 3.3 70B via Groq
        </p>
      </div>

      <div style="line-height:1.7;color:#c0c4d6;font-size:14px;">
        <p style="margin:8px 0;line-height:1.7;color:#c0c4d6;">${html}</p>
      </div>

      <div style="text-align:center;padding-top:20px;margin-top:24px;border-top:1px solid rgba(255,255,255,0.08);font-size:11px;color:#5a5e73;">
        Generated by SpendSmart AI • ${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
      </div>
    `;
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
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          className="btn-primary"
          onClick={handleExport}
          disabled={exporting || aiLoading}
          style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
        >
          <LuFileDown />
          {exporting ? 'Generating...' : 'Export PDF'}
        </button>
        <button
          className="btn-primary"
          onClick={handleAIExport}
          disabled={exporting || aiLoading}
          style={{
            fontSize: '0.8rem',
            padding: '0.5rem 1rem',
            background: 'linear-gradient(135deg, #7b2ff7, #f72f8e)',
            border: 'none',
          }}
        >
          <LuSparkles />
          {aiLoading ? 'AI Analyzing...' : 'AI Report ✨'}
        </button>
      </div>

      {/* Hidden regular report layout */}
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

      {/* Hidden AI report container */}
      <div
        ref={aiReportRef}
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
      />
    </>
  );
}
