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

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function todayIso(): string {
  const now = new Date();
  const tz = new Date(now.toLocaleString("en-US", { timeZone: "Europe/Copenhagen" }));
  return `${tz.getFullYear()}-${pad2(tz.getMonth() + 1)}-${pad2(tz.getDate())}`;
}

export function monthStartIso(year: number, monthIndex: number): string {
  return `${year}-${pad2(monthIndex + 1)}-01`;
}

export function monthEndIso(year: number, monthIndex: number): string {
  const last = new Date(year, monthIndex + 1, 0).getDate();
  return `${year}-${pad2(monthIndex + 1)}-${pad2(last)}`;
}

export function shiftMonth(year: number, monthIndex: number, delta: number): { year: number; monthIndex: number } {
  const date = new Date(year, monthIndex + delta, 1);
  return { year: date.getFullYear(), monthIndex: date.getMonth() };
}

export function formatMonthTitle(year: number, monthIndex: number): string {
  return new Intl.DateTimeFormat("da-DK", { month: "long", year: "numeric" }).format(new Date(year, monthIndex, 1));
}

export const MONTH_LABELS_DA = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"];

export function inDateRange(iso: string, from: string, to: string): boolean {
  if (from && iso < from) return false;
  if (to && iso > to) return false;
  return true;
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
