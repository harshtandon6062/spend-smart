import { useState } from 'react';
import { LuLayoutDashboard, LuLightbulb, LuSlidersHorizontal, LuWallet, LuFileDown, LuArrowLeft } from 'react-icons/lu';
import SummaryBar from './SummaryBar';
import CategoryChart from './CategoryChart';
import DailyChart from './DailyChart';
import MerchantChart from './MerchantChart';
import WeekdayChart from './WeekdayChart';
import InsightCards from './InsightCards';
import Simulator from './Simulator';
import BudgetPlanner from './BudgetPlanner';
import PDFExport from './PDFExport';

export default function Dashboard({ analytics, recommendations, onReset }) {
  const [activeSection, setActiveSection] = useState('overview');

  const navItems = [
    { id: 'overview', label: 'Overview', icon: <LuLayoutDashboard /> },
    { id: 'insights', label: 'Insights', icon: <LuLightbulb /> },
    { id: 'simulator', label: 'Simulator', icon: <LuSlidersHorizontal /> },
    { id: 'budget', label: 'Budget', icon: <LuWallet /> },
  ];

  const scrollTo = (id) => {
    setActiveSection(id);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  // Deduplicate savings: take max per category to avoid overlapping recommendations
  const savingsByCategory = {};
  recommendations.forEach((r) => {
    savingsByCategory[r.category] = Math.max(
      savingsByCategory[r.category] || 0,
      r.savings_estimate
    );
  });
  const rawSavings = Object.values(savingsByCategory).reduce((s, v) => s + v, 0);
  // Cap at 30% of total spend — a realistic savings ceiling
  const totalSavings = Math.min(rawSavings, analytics.total_spend * 0.3);

  return (
    <div>
      {/* Navigation */}
      <nav className="dashboard-nav">
        <div className="nav-inner">
          <span className="nav-brand" onClick={onReset} style={{ cursor: 'pointer' }}>
            <LuArrowLeft style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
            SpendSmart
          </span>
          <ul className="nav-links">
            {navItems.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  className={activeSection === item.id ? 'active' : ''}
                  onClick={(e) => { e.preventDefault(); scrollTo(item.id); }}
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
          <PDFExport analytics={analytics} recommendations={recommendations} />
        </div>
      </nav>

      <div className="dashboard-container" id="dashboard-content">
        {/* Summary Stats */}
        <section id="overview" className="section-animate">
          <SummaryBar analytics={analytics} totalSavings={totalSavings} />
        </section>

        {/* Charts */}
        <section className="section-animate">
          <h2 className="section-title">
            <LuLayoutDashboard className="title-icon" /> Spending Analysis
          </h2>
          <div className="charts-grid">
            <CategoryChart data={analytics.category_totals} />
            <DailyChart data={analytics.daily_spend} />
            <MerchantChart data={analytics.top_merchants} />
            <WeekdayChart data={analytics.weekday_vs_weekend} />
          </div>
        </section>

        {/* Insights */}
        <section id="insights" className="section-animate">
          <h2 className="section-title">
            <LuLightbulb className="title-icon" /> Smart Insights
          </h2>
          <InsightCards recommendations={recommendations} />
        </section>

        {/* Simulator */}
        <section id="simulator" className="section-animate">
          <h2 className="section-title">
            <LuSlidersHorizontal className="title-icon" /> What-If Savings Simulator
          </h2>
          <Simulator categories={analytics.category_totals} />
        </section>

        {/* Budget */}
        <section id="budget" className="section-animate" style={{ marginBottom: '4rem' }}>
          <h2 className="section-title">
            <LuWallet className="title-icon" /> Monthly Budget Planner
          </h2>
          <BudgetPlanner categories={analytics.category_totals} />
        </section>
      </div>
    </div>
  );
}
