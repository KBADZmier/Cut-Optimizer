export default function ConfidenceBadge({ value }) {
  const level = value >= 0.9 ? "high" : value >= 0.8 ? "medium" : "low";

  return (
    <span className={`confidence confidence--${level}`}>
      {Math.round(value * 100)}%
    </span>
  );
}
