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

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return new Intl.DateTimeFormat("da-DK", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Copenhagen",
  }).format(date);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return new Intl.DateTimeFormat("da-DK", {
    dateStyle: "medium",
    timeZone: "Europe/Copenhagen",
  }).format(date);
}
