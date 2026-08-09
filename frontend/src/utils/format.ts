export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString();
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export function formatStopCities(
  stops: Array<{ stop_type: string; city: string | null }>,
  type: "PICKUP" | "DELIVERY",
): string {
  return (
    stops
      .filter((stop) => stop.stop_type === type)
      .map((stop) => stop.city)
      .filter(Boolean)
      .join(", ") || "—"
  );
}

export function isToday(value: string): boolean {
  const date = new Date(value);
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
}
