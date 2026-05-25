/**
 * Currency, date, and percentage formatters for Indian locale.
 */

export const formatCurrency = (amount) => {
  if (amount == null) return '₹0';
  return `₹${Number(amount).toLocaleString('en-IN', {
    maximumFractionDigits: 0,
  })}`;
};

export const formatPercent = (value) => {
  if (value == null) return '0%';
  return `${Number(value).toFixed(1)}%`;
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
  });
};

export const formatDateFull = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};
