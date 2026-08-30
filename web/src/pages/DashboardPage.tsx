import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Dashboard } from "../api";
import { useAuth } from "../auth";
import { formatDkk } from "../money";

export default function DashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api.dashboard(token).then(setData).catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-stone-500">How much you have spent, by project tag and vendor</p>
        </div>
        <Link
          to="/upload"
          className="rounded-lg bg-brand-600 px-4 py-2 text-center text-sm font-medium text-white hover:bg-brand-700"
        >
          Scan a receipt
        </Link>
      </div>

      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="This month" value={formatDkk(data.this_month_ore)} />
            <Stat label="All time" value={formatDkk(data.all_time_ore)} />
            <Stat label="Receipts" value={String(data.receipt_count)} />
          </div>

          <section className="rounded-2xl border border-stone-200 bg-white p-4">
            <h3 className="font-semibold">Spend by tag</h3>
            {data.by_tag.length === 0 ? (
              <p className="mt-2 text-sm text-stone-500">
                No tags yet. Create projects on the{" "}
                <Link className="text-brand-700 underline" to="/tags">
                  Tags
                </Link>{" "}
                page, then add them on a receipt.
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {data.by_tag.map((row) => (
                  <li key={row.tag.id} className="flex items-center justify-between gap-3 text-sm">
                    <span className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full" style={{ background: row.tag.color }} />
                      {row.tag.name}
                      <span className="text-stone-400">({row.receipt_count})</span>
                    </span>
                    <span className="font-medium">{formatDkk(row.total_ore)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-2xl border border-stone-200 bg-white p-4">
            <h3 className="font-semibold">Spend by vendor</h3>
            {data.by_vendor.length === 0 ? (
              <p className="mt-2 text-sm text-stone-500">Upload your first receipt to start the ledger.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {data.by_vendor.map((row) => (
                  <li key={row.vendor_name} className="flex items-center justify-between gap-3 text-sm">
                    <span>
                      {row.vendor_name} <span className="text-stone-400">({row.receipt_count})</span>
                    </span>
                    <span className="font-medium">{formatDkk(row.total_ore)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-4">
      <p className="text-sm text-stone-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
