import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, Tooltip, Legend,
} from 'chart.js';
import { formatCurrency, formatDate } from '../utils/formatters';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function DailyChart({ data }) {
  const chartData = {
    labels: data.map((d) => formatDate(d.date)),
    datasets: [
      {
        label: 'Daily Spend',
        data: data.map((d) => d.total),
        backgroundColor: data.map((_, i) => {
          const isWeekend = [5, 6].includes(new Date(data[i].date).getDay());
          return isWeekend ? 'rgba(247, 47, 142, 0.6)' : 'rgba(0, 212, 255, 0.5)';
        }),
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17, 22, 56, 0.95)',
        titleFont: { family: 'Inter', weight: '600' },
        bodyFont: { family: 'Inter' },
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: (ctx) => ` Spent: ${formatCurrency(ctx.raw)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#5a5e73', font: { family: 'Inter', size: 10 }, maxRotation: 45 },
      },
      y: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#5a5e73',
          font: { family: 'Inter', size: 11 },
          callback: (v) => `₹${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}`,
        },
      },
    },
    animation: { duration: 1200, easing: 'easeOutQuart' },
  };

  return (
    <div className="chart-card">
      <h3>Daily Spending <span style={{ fontSize: '0.75rem', color: '#f72f8e', marginLeft: '0.5rem' }}>● Weekend</span></h3>
      <div style={{ height: '280px' }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
