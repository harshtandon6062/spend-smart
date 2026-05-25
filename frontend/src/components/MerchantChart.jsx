import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, Tooltip, Legend,
} from 'chart.js';
import { formatCurrency } from '../utils/formatters';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function MerchantChart({ data }) {
  const chartData = {
    labels: data.map((d) => d.merchant),
    datasets: [
      {
        label: 'Total Spend',
        data: data.map((d) => d.total),
        backgroundColor: [
          'rgba(0, 212, 255, 0.6)',
          'rgba(123, 47, 247, 0.6)',
          'rgba(247, 47, 142, 0.6)',
          'rgba(0, 230, 138, 0.6)',
          'rgba(255, 179, 71, 0.6)',
        ],
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    indexAxis: 'y',
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
          label: (ctx) => {
            const item = data[ctx.dataIndex];
            return ` ${formatCurrency(item.total)} (${item.count} visits)`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#5a5e73',
          font: { family: 'Inter', size: 11 },
          callback: (v) => `₹${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}`,
        },
      },
      y: {
        grid: { display: false },
        ticks: { color: '#8b8fa3', font: { family: 'Inter', size: 12, weight: '500' } },
      },
    },
    animation: { duration: 1200, easing: 'easeOutQuart' },
  };

  return (
    <div className="chart-card">
      <h3>Top Merchants</h3>
      <div style={{ height: '280px' }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
