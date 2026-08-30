import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, CalendarDay } from "../api";
import { useAuth } from "../auth";
import { formatDkk } from "../money";

const WEEKDAYS = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"];

export default function CalendarPage() {
  const { token } = useAuth();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [days, setDays] = useState<CalendarDay[]>([]);
  const [selected, setSelected] = useState<CalendarDay | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api
      .calendar(token, year, month)
      .then((data) => {
        setDays(data);
        setSelected(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token, year, month]);

  function shift(delta: number) {
    const date = new Date(year, month - 1 + delta, 1);
    setYear(date.getFullYear());
    setMonth(date.getMonth() + 1);
  }

  const first = new Date(year, month - 1, 1);
  const mondayIndex = (first.getDay() + 6) % 7;
  const blanks = Array.from({ length: mondayIndex });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          {first.toLocaleDateString("da-DK", { month: "long", year: "numeric" })}
        </h2>
        <div className="flex gap-2">
          <button className="rounded-lg border px-3 py-1" onClick={() => shift(-1)}>
            ←
          </button>
          <button className="rounded-lg border px-3 py-1" onClick={() => shift(1)}>
            →
          </button>
        </div>
      </div>

      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-stone-500">
        {WEEKDAYS.map((day) => (
          <div key={day} className="py-1">
            {day}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {blanks.map((_, index) => (
          <div key={`b${index}`} />
        ))}
        {days.map((day) => {
          const number = Number(day.date.slice(-2));
          const active = selected?.date === day.date;
          return (
            <button
              key={day.date}
              type="button"
              onClick={() => setSelected(day)}
              className={`min-h-16 rounded-lg border p-1 text-left text-xs ${
                day.receipt_count ? "border-brand-200 bg-brand-50" : "border-stone-200 bg-white"
              } ${active ? "ring-2 ring-brand-600" : ""}`}
            >
              <span className="font-medium">{number}</span>
              {day.receipt_count > 0 && (
                <p className="mt-1 text-[11px] text-brand-800">
                  {day.receipt_count} · {formatDkk(day.total_ore)}
                </p>
              )}
            </button>
          );
        })}
      </div>

      {selected && (
        <section className="rounded-2xl border border-stone-200 bg-white p-4">
          <h3 className="font-semibold">{selected.date}</h3>
          {selected.receipts.length === 0 ? (
            <p className="mt-2 text-sm text-stone-500">No receipts this day.</p>
          ) : (
            <ul className="mt-2 divide-y">
              {selected.receipts.map((receipt) => (
                <li key={receipt.id} className="flex items-center justify-between py-2 text-sm">
                  <Link to={`/receipts/${receipt.id}`} className="text-brand-700 hover:underline">
                    {receipt.vendor_name}
                    {receipt.store_name ? ` · ${receipt.store_name}` : ""}
                  </Link>
                  <span>{formatDkk(receipt.total_ore)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
