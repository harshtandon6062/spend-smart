import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, Tooltip, Legend,
} from 'chart.js';
import { formatCurrency } from '../utils/formatters';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function WeekdayChart({ data }) {
  const categories = Object.keys(data.categories || {});

  const chartData = {
    labels: categories,
    datasets: [
      {
        label: 'Weekday Avg',
        data: categories.map((c) => data.categories[c].weekday),
        backgroundColor: 'rgba(0, 212, 255, 0.6)',
        borderRadius: 4,
        borderSkipped: false,
      },
      {
        label: 'Weekend Avg',
        data: categories.map((c) => data.categories[c].weekend),
        backgroundColor: 'rgba(247, 47, 142, 0.6)',
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#8b8fa3',
          font: { family: 'Inter', size: 11 },
          usePointStyle: true,
          pointStyleWidth: 10,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(17, 22, 56, 0.95)',
        titleFont: { family: 'Inter', weight: '600' },
        bodyFont: { family: 'Inter' },
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.raw)}/day`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#5a5e73', font: { family: 'Inter', size: 11 } },
      },
      y: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#5a5e73',
          font: { family: 'Inter', size: 11 },
          callback: (v) => `₹${v}`,
        },
      },
    },
    animation: { duration: 1200, easing: 'easeOutQuart' },
  };

  return (
    <div className="chart-card">
      <h3>Weekday vs Weekend</h3>
      <div style={{ height: '280px' }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
