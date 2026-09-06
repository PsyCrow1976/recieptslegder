export function formatDkk(ore: number | null | undefined): string {
  if (ore === null || ore === undefined) return "—";
  const sign = ore < 0 ? "-" : "";
  const abs = Math.abs(ore);
  const kroner = Math.floor(abs / 100);
  const rest = abs % 100;
  const grouped = kroner.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped},${rest.toString().padStart(2, "0")} kr`;
}

export function parseDkkInput(value: string): number {
  const cleaned = value.trim().replace(/\s/g, "").replace("kr", "").replace("KR", "");
  if (!cleaned) return 0;
  let normalized = cleaned;
  if (cleaned.includes(",") && cleaned.includes(".")) {
    normalized = cleaned.replace(/\./g, "").replace(",", ".");
  } else if (cleaned.includes(",")) {
    normalized = cleaned.replace(",", ".");
  }
  const amount = Number(normalized);
  if (Number.isNaN(amount)) return 0;
  return Math.round(amount * 100);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = iso.length <= 10 ? new Date(`${iso}T12:00:00`) : new Date(iso);
  return new Intl.DateTimeFormat("da-DK", {
    dateStyle: "medium",
    timeZone: "Europe/Copenhagen",
  }).format(date);
}

export function todayIso(): string {
  const now = new Date();
  const tz = new Date(now.toLocaleString("en-US", { timeZone: "Europe/Copenhagen" }));
  const year = tz.getFullYear();
  const month = String(tz.getMonth() + 1).padStart(2, "0");
  const day = String(tz.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export const COLORS = [
  "#0f766e",
  "#1e3a5f",
  "#9a3412",
  "#7c3aed",
  "#be185d",
  "#0369a1",
  "#4d7c0f",
  "#b45309",
];
