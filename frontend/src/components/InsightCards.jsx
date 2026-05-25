import {
  LuTrendingDown, LuTriangleAlert, LuCalendar, LuCreditCard,
  LuMapPin, LuCircleAlert, LuTrainFront, LuTarget, LuPiggyBank, LuStore,
} from 'react-icons/lu';
import { formatCurrency } from '../utils/formatters';

const ICON_MAP = {
  TrendingDown: LuTrendingDown,
  AlertTriangle: LuTriangleAlert,
  Calendar: LuCalendar,
  CreditCard: LuCreditCard,
  MapPin: LuMapPin,
  AlertCircle: LuCircleAlert,
  Train: LuTrainFront,
  Target: LuTarget,
  PiggyBank: LuPiggyBank,
  Store: LuStore,
};

export default function InsightCards({ recommendations }) {
  return (
    <div className="insights-list">
      {recommendations.map((rec, i) => {
        const IconComponent = ICON_MAP[rec.icon] || LuAlertCircle;
        return (
          <div
            key={i}
            className={`insight-card priority-${rec.priority}`}
            style={{ animationDelay: `${i * 0.06}s` }}
          >
            <div className="insight-icon">
              <IconComponent size={20} />
            </div>
            <div className="insight-content">
              <div className="insight-title">{rec.title}</div>
              <div className="insight-desc">{rec.description}</div>
            </div>
            {rec.savings_estimate > 0 && (
              <div className="savings-badge">
                Save {formatCurrency(rec.savings_estimate)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
