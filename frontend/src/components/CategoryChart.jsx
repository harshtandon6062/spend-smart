import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { formatCurrency } from '../utils/formatters';

ChartJS.register(ArcElement, Tooltip, Legend);

const COLORS = [
  '#00d4ff', '#7b2ff7', '#f72f8e', '#00e68a',
  '#ffb347', '#ff4757', '#5f6fff', '#ff6b9d',
];

export default function CategoryChart({ data }) {
  const chartData = {
    labels: data.map((d) => d.category),
    datasets: [
      {
        data: data.map((d) => d.total),
        backgroundColor: COLORS.slice(0, data.length),
        borderWidth: 0,
        hoverOffset: 8,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#8b8fa3',
          font: { family: 'Inter', size: 12 },
          padding: 12,
          usePointStyle: true,
          pointStyleWidth: 10,
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
          label: (ctx) => {
            const item = data[ctx.dataIndex];
            return ` ${item.category}: ${formatCurrency(item.total)} (${item.percentage}%)`;
          },
        },
      },
    },
    cutout: '65%',
    animation: { animateRotate: true, duration: 1000 },
  };

  return (
    <div className="chart-card">
      <h3>Category Breakdown</h3>
      <div style={{ height: '280px' }}>
        <Doughnut data={chartData} options={options} />
      </div>
    </div>
  );
}
