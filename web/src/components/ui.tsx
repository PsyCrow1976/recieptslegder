import { Link } from "react-router-dom";
import { COLORS, formatDkk } from "../money";

export function Money({ ore, className = "" }: { ore: number; className?: string }) {
  const tone = ore > 0 ? "text-emerald-700" : ore < 0 ? "text-rose-700" : "text-stone-600";
  return <span className={`tabular-nums font-medium ${tone} ${className}`}>{formatDkk(ore)}</span>;
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-3xl text-ink">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-stone-500">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function EmptyState({
  title,
  body,
  to,
  cta,
}: {
  title: string;
  body: string;
  to?: string;
  cta?: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-stone-300 bg-white/70 px-6 py-12 text-center">
      <h2 className="text-xl text-ink">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-stone-500">{body}</p>
      {to && cta ? (
        <Link
          to={to}
          className="mt-5 inline-flex rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          {cta}
        </Link>
      ) : null}
    </div>
  );
}

export function ColorField({ value, onChange }: { value: string; onChange: (color: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {COLORS.map((color) => (
        <button
          key={color}
          type="button"
          onClick={() => onChange(color)}
          className={`h-7 w-7 rounded-full border-2 ${value === color ? "border-ink" : "border-transparent"}`}
          style={{ backgroundColor: color }}
          aria-label={color}
        />
      ))}
    </div>
  );
}

export function Chip({ label, color }: { label: string; color?: string }) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: `${color || "#0f766e"}22`, color: color || "#0f766e" }}
    >
      {label}
    </span>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm font-medium text-stone-700">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-brand-600 focus:ring-2 focus:ring-brand-100";

export const btnPrimary =
  "rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60";

export const btnGhost =
  "rounded-lg px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-100";

export const cardClass = "rounded-2xl border border-stone-200 bg-white p-5 shadow-sm";
