import { LuIndianRupee, LuCalendarDays, LuTrophy, LuPiggyBank } from 'react-icons/lu';
import { formatCurrency, formatDateFull } from '../utils/formatters';

export default function SummaryBar({ analytics, totalSavings }) {
  const topCategory = analytics.category_totals[0];

  const stats = [
    {
      icon: <LuIndianRupee />,
      label: 'Total Spend',
      value: formatCurrency(analytics.total_spend),
      color: '#00d4ff',
    },
    {
      icon: <LuCalendarDays />,
      label: 'Daily Average',
      value: formatCurrency(analytics.daily_average),
      color: '#7b2ff7',
    },
    {
      icon: <LuTrophy />,
      label: 'Top Category',
      value: `${topCategory?.category || '—'} (${topCategory?.percentage || 0}%)`,
      color: '#f72f8e',
    },
    {
      icon: <LuPiggyBank />,
      label: 'Potential Savings',
      value: formatCurrency(totalSavings),
      color: '#00e68a',
    },
  ];

  return (
    <div className="stats-grid">
      {stats.map((stat, i) => (
        <div className="stat-card" key={i}>
          <div className="stat-icon" style={{ background: `${stat.color}15`, color: stat.color }}>
            {stat.icon}
          </div>
          <span className="stat-label">{stat.label}</span>
          <span className="stat-value">{stat.value}</span>
        </div>
      ))}
    </div>
  );
}
