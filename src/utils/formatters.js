export function formatMm(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
