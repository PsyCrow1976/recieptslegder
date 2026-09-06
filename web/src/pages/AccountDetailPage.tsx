import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type AccountSummary, type Movement } from "../api";
import { useAuth } from "../auth";
import { Chip, EmptyState, Field, Money, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";
import {
  formatDate,
  formatDkk,
  formatMonthTitle,
  inDateRange,
  MONTH_LABELS_DA,
  monthEndIso,
  monthStartIso,
  parseDkkInput,
  shiftMonth,
  todayIso,
} from "../money";

function oreInput(ore: number): string {
  return formatDkk(ore).replace(" kr", "");
}

function balanceAt(
  account: AccountSummary,
  movements: Movement[],
  throughInclusive: string | null,
  beforeExclusive: string | null,
): number {
  let total = account.opening_balance_ore;
  for (const movement of movements) {
    if (account.opening_on && movement.posted_on < account.opening_on) continue;
    if (beforeExclusive && movement.posted_on >= beforeExclusive) continue;
    if (throughInclusive && movement.posted_on > throughInclusive) continue;
    total += movement.amount_ore;
  }
  return total;
}

type CategoryYearRow = {
  key: string;
  name: string;
  months: number[];
  year: number;
};

function categoryLabel(movement: Movement): { key: string; name: string } {
  const first = movement.categories[0];
  if (!first) return { key: "other", name: "Other" };
  return { key: first.id, name: first.name };
}

function yearCategoryRows(movements: Movement[], year: number, income: boolean): CategoryYearRow[] {
  const prefix = `${year}-`;
  const map = new Map<string, CategoryYearRow>();
  for (const movement of movements) {
    if (!movement.posted_on.startsWith(prefix)) continue;
    if (income && movement.amount_ore <= 0) continue;
    if (!income && movement.amount_ore >= 0) continue;
    const month = Number(movement.posted_on.slice(5, 7)) - 1;
    const { key, name } = categoryLabel(movement);
    let row = map.get(key);
    if (!row) {
      row = { key, name, months: Array(12).fill(0), year: 0 };
      map.set(key, row);
    }
    row.months[month] += movement.amount_ore;
    row.year += movement.amount_ore;
  }
  return [...map.values()].sort((a, b) => {
    if (a.key === "other") return 1;
    if (b.key === "other") return -1;
    return a.name.localeCompare(b.name, "da");
  });
}

function totalsFromRows(rows: CategoryYearRow[]): number[] {
  const months = Array(12).fill(0);
  for (const row of rows) {
    row.months.forEach((value, index) => {
      months[index] += value;
    });
  }
  return months;
}

function Cell({ ore }: { ore: number }) {
  if (!ore) return <span className="text-stone-300">—</span>;
  return <Money ore={ore} />;
}

function YearMatrix({
  title,
  rows,
  totals,
  onMonth,
}: {
  title: string;
  rows: CategoryYearRow[];
  totals: number[];
  onMonth: (monthIndex: number) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
            <th className="sticky left-0 bg-stone-50 px-3 py-3 font-medium">{title}</th>
            {MONTH_LABELS_DA.map((label, index) => (
              <th key={label} className="px-2 py-3 text-right font-medium">
                <button type="button" className="hover:text-brand-700 hover:underline" onClick={() => onMonth(index)}>
                  {label}
                </button>
              </th>
            ))}
            <th className="px-3 py-3 text-right font-medium">Year</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="px-3 py-4 text-stone-500" colSpan={14}>
                No {title.toLowerCase()} this year.
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.key} className="border-t border-stone-100">
                <td className="sticky left-0 bg-white px-3 py-2 font-medium">{row.name}</td>
                {row.months.map((ore, index) => (
                  <td key={index} className="whitespace-nowrap px-2 py-2 text-right">
                    <Cell ore={ore} />
                  </td>
                ))}
                <td className="whitespace-nowrap px-3 py-2 text-right font-medium">
                  <Cell ore={row.year} />
                </td>
              </tr>
            ))
          )}
          <tr className="border-t border-stone-200 bg-stone-50 font-medium">
            <td className="sticky left-0 bg-stone-50 px-3 py-2">Total</td>
            {totals.map((ore, index) => (
              <td key={index} className="whitespace-nowrap px-2 py-2 text-right">
                <Cell ore={ore} />
              </td>
            ))}
            <td className="whitespace-nowrap px-3 py-2 text-right">
              <Cell ore={totals.reduce((sum, value) => sum + value, 0)} />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function EntryRow({ movement }: { movement: Movement }) {
  return (
    <Link
      to={`/entries/${movement.id}`}
      className="flex items-center justify-between gap-4 border-b border-stone-100 px-4 py-3 last:border-b-0 hover:bg-stone-50"
    >
      <div>
        <p className="font-medium">{movement.description || movement.vendor?.name || "Entry"}</p>
        <p className="text-xs text-stone-500">
          {formatDate(movement.posted_on)}
          {movement.vendor ? ` · ${movement.vendor.name}` : ""}
          {movement.items.length ? ` · ${movement.items.length} items` : ""}
        </p>
      </div>
      <Money ore={movement.amount_ore} />
    </Link>
  );
}

export default function AccountDetailPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [error, setError] = useState("");
  const [opening, setOpening] = useState("0");
  const [openingOn, setOpeningOn] = useState("");
  const [saving, setSaving] = useState(false);
  const [view, setView] = useState<"list" | "month" | "year">("month");
  const [listFrom, setListFrom] = useState("");
  const [listTo, setListTo] = useState(todayIso());
  const today = todayIso();
  const [monthYear, setMonthYear] = useState(() => Number(today.slice(0, 4)));
  const [monthIndex, setMonthIndex] = useState(() => Number(today.slice(5, 7)) - 1);

  function applyAccount(a: AccountSummary) {
    setAccount(a);
    setOpening(oreInput(a.opening_balance_ore));
    setOpeningOn(a.opening_on || "");
    if (a.opening_on && !listFrom) setListFrom(a.opening_on);
  }

  useEffect(() => {
    if (!id) return;
    Promise.all([api.account(token!, id), api.movements(token!, { accountId: id })])
      .then(([a, m]) => {
        applyAccount(a);
        setMovements(m);
      })
      .catch((err: Error) => setError(err.message));
  }, [id, token]);

  async function saveStart(event: FormEvent) {
    event.preventDefault();
    if (!id) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api.updateAccount(token!, id, {
        opening_balance_ore: parseDkkInput(opening),
        opening_on: openingOn || null,
      });
      applyAccount(updated);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!id || !confirm("Delete this account and all of its entries?")) return;
    await api.deleteAccount(token!, id);
    navigate("/accounts");
  }

  const listRows = useMemo(
    () => movements.filter((row) => inDateRange(row.posted_on, listFrom, listTo)),
    [movements, listFrom, listTo],
  );

  const monthFrom = monthStartIso(monthYear, monthIndex);
  const monthTo = monthEndIso(monthYear, monthIndex);
  const monthRows = useMemo(
    () =>
      movements
        .filter((row) => inDateRange(row.posted_on, monthFrom, monthTo))
        .slice()
        .sort((a, b) => a.posted_on.localeCompare(b.posted_on) || a.created_at.localeCompare(b.created_at)),
    [movements, monthFrom, monthTo],
  );
  const incomeOre = monthRows.filter((row) => row.amount_ore > 0).reduce((sum, row) => sum + row.amount_ore, 0);
  const expenseOre = monthRows.filter((row) => row.amount_ore < 0).reduce((sum, row) => sum + row.amount_ore, 0);
  const monthStartBalance = account ? balanceAt(account, movements, null, monthFrom) : 0;
  const monthEndBalance = account ? balanceAt(account, movements, monthTo, null) : 0;
  const monthLines = useMemo(() => {
    let running = monthStartBalance;
    return monthRows.map((movement) => {
      running += movement.amount_ore;
      return { movement, balance: running };
    });
  }, [monthRows, monthStartBalance]);

  const incomeYearRows = useMemo(() => yearCategoryRows(movements, monthYear, true), [movements, monthYear]);
  const expenseYearRows = useMemo(() => yearCategoryRows(movements, monthYear, false), [movements, monthYear]);
  const incomeYearTotals = useMemo(() => totalsFromRows(incomeYearRows), [incomeYearRows]);
  const expenseYearTotals = useMemo(() => totalsFromRows(expenseYearRows), [expenseYearRows]);
  const yearMonthBalances = useMemo(() => {
    if (!account) return Array(12).fill(0);
    return Array.from({ length: 12 }, (_, month) =>
      balanceAt(account, movements, monthEndIso(monthYear, month), null),
    );
  }, [account, movements, monthYear]);

  if (error && !account) return <p className="text-rose-700">{error}</p>;
  if (!account) return <p className="text-stone-500">Loading…</p>;

  return (
    <div>
      <PageHeader
        title={account.name}
        subtitle={`${account.platform.name} · ${account.currency}${account.account_number ? ` · ${account.account_number}` : ""}`}
        action={
          <div className="flex gap-2">
            <Link
              to="/entries/import"
              className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50"
            >
              Import CSV
            </Link>
            <Link to={`/entries/new?account=${account.id}`} className={btnPrimary}>
              Add entry
            </Link>
            <button type="button" className={btnGhost} onClick={remove}>
              Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Current balance</p>
          <div className="mt-2 text-2xl">
            <Money ore={account.balance_ore} className="text-2xl" />
          </div>
        </div>
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Start amount</p>
          <div className="mt-2">
            <Money ore={account.opening_balance_ore} />
          </div>
          <p className="mt-1 text-xs text-stone-500">
            {account.opening_on ? `At the start of ${formatDate(account.opening_on)}` : "No start date — all entries are counted"}
          </p>
        </div>
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Owners</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {account.owners.map((owner) => (
              <Chip key={owner.id} label={owner.name} color={owner.color} />
            ))}
          </div>
        </div>
      </div>

      <form onSubmit={saveStart} className={`${cardClass} mt-4 grid gap-4 sm:grid-cols-3`}>
        <Field label="Start amount">
          <input className={inputClass} value={opening} onChange={(e) => setOpening(e.target.value)} />
        </Field>
        <Field label="Start date">
          <input type="date" className={inputClass} value={openingOn} onChange={(e) => setOpeningOn(e.target.value)} />
        </Field>
        <div className="flex items-end">
          <button className={btnPrimary} type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save start amount"}
          </button>
        </div>
        {error ? <p className="sm:col-span-3 text-sm text-rose-700">{error}</p> : null}
      </form>

      <div className="mt-8 flex gap-2">
        <button
          type="button"
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${view === "month" ? "bg-brand-600 text-white" : "bg-white text-stone-700 border border-stone-300"}`}
          onClick={() => setView("month")}
        >
          Month
        </button>
        <button
          type="button"
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${view === "year" ? "bg-brand-600 text-white" : "bg-white text-stone-700 border border-stone-300"}`}
          onClick={() => setView("year")}
        >
          Year
        </button>
        <button
          type="button"
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${view === "list" ? "bg-brand-600 text-white" : "bg-white text-stone-700 border border-stone-300"}`}
          onClick={() => setView("list")}
        >
          List
        </button>
      </div>

      {view === "list" && (
        <section className="mt-4">
          <div className={`${cardClass} mb-4 grid gap-4 sm:grid-cols-3`}>
            <Field label="From">
              <input type="date" className={inputClass} value={listFrom} onChange={(e) => setListFrom(e.target.value)} />
            </Field>
            <Field label="To">
              <input type="date" className={inputClass} value={listTo} onChange={(e) => setListTo(e.target.value)} />
            </Field>
            <p className="self-end text-sm text-stone-500">{listRows.length} entries</p>
          </div>
          {listRows.length === 0 ? (
            <EmptyState title="No entries in this range" body="Change the dates, import a CSV, or add an entry." />
          ) : (
            <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
              {listRows.map((movement) => (
                <EntryRow key={movement.id} movement={movement} />
              ))}
            </div>
          )}
        </section>
      )}

      {view === "year" && (
        <section className="mt-4 space-y-4">
          <div className="flex items-center justify-between">
            <button type="button" className={btnGhost} onClick={() => setMonthYear((year) => year - 1)}>
              Previous
            </button>
            <h2 className="text-xl text-ink">{monthYear}</h2>
            <button type="button" className={btnGhost} onClick={() => setMonthYear((year) => year + 1)}>
              Next
            </button>
          </div>
          <YearMatrix
            title="Income"
            rows={incomeYearRows}
            totals={incomeYearTotals}
            onMonth={(index) => {
              setMonthIndex(index);
              setView("month");
            }}
          />
          <YearMatrix
            title="Expenses"
            rows={expenseYearRows}
            totals={expenseYearTotals}
            onMonth={(index) => {
              setMonthIndex(index);
              setView("month");
            }}
          />
          <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
                  <th className="sticky left-0 bg-stone-50 px-3 py-3 font-medium">Balance</th>
                  {MONTH_LABELS_DA.map((label) => (
                    <th key={label} className="px-2 py-3 text-right font-medium">
                      {label}
                    </th>
                  ))}
                  <th className="px-3 py-3 text-right font-medium">Year</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="sticky left-0 bg-white px-3 py-3 font-medium">End of month</td>
                  {yearMonthBalances.map((ore, index) => (
                    <td key={index} className="whitespace-nowrap px-2 py-3 text-right">
                      <Money ore={ore} />
                    </td>
                  ))}
                  <td className="whitespace-nowrap px-3 py-3 text-right font-medium">
                    <Money ore={yearMonthBalances[11] ?? 0} />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}

      {view === "month" && (
        <section className="mt-4 space-y-4">
          <div className="flex items-center justify-between">
            <button
              type="button"
              className={btnGhost}
              onClick={() => {
                const next = shiftMonth(monthYear, monthIndex, -1);
                setMonthYear(next.year);
                setMonthIndex(next.monthIndex);
              }}
            >
              Previous
            </button>
            <h2 className="text-xl capitalize text-ink">{formatMonthTitle(monthYear, monthIndex)}</h2>
            <button
              type="button"
              className={btnGhost}
              onClick={() => {
                const next = shiftMonth(monthYear, monthIndex, 1);
                setMonthYear(next.year);
                setMonthIndex(next.monthIndex);
              }}
            >
              Next
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className={cardClass}>
              <p className="text-xs uppercase tracking-wide text-stone-500">Start of month</p>
              <div className="mt-2 text-xl">
                <Money ore={monthStartBalance} className="text-xl" />
              </div>
              <p className="mt-1 text-xs text-stone-500">{formatDate(monthFrom)}</p>
            </div>
            <div className={cardClass}>
              <p className="text-xs uppercase tracking-wide text-stone-500">End of month</p>
              <div className="mt-2 text-xl">
                <Money ore={monthEndBalance} className="text-xl" />
              </div>
              <p className="mt-1 text-xs text-stone-500">{formatDate(monthTo)}</p>
            </div>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Entry</th>
                  <th className="px-4 py-3 text-right font-medium text-emerald-800">Income</th>
                  <th className="px-4 py-3 text-right font-medium text-rose-800">Expenses</th>
                  <th className="px-4 py-3 text-right font-medium">Balance</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-stone-100 bg-stone-50/80">
                  <td className="px-4 py-2 text-stone-500" colSpan={4}>
                    Start of month
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Money ore={monthStartBalance} />
                  </td>
                </tr>
                {monthLines.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-stone-500" colSpan={5}>
                      No income or expenses this month.
                    </td>
                  </tr>
                ) : (
                  monthLines.map(({ movement, balance }) => (
                    <tr key={movement.id} className="border-b border-stone-100 hover:bg-stone-50">
                      <td className="whitespace-nowrap px-4 py-3 text-stone-500">{formatDate(movement.posted_on)}</td>
                      <td className="px-4 py-3">
                        <Link to={`/entries/${movement.id}`} className="font-medium text-ink hover:underline">
                          {movement.description || movement.vendor?.name || "Entry"}
                        </Link>
                        {movement.vendor && movement.vendor.name !== movement.description ? (
                          <p className="text-xs text-stone-500">{movement.vendor.name}</p>
                        ) : null}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        {movement.amount_ore > 0 ? <Money ore={movement.amount_ore} /> : ""}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        {movement.amount_ore < 0 ? <Money ore={movement.amount_ore} /> : ""}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        <Money ore={balance} />
                      </td>
                    </tr>
                  ))
                )}
                <tr className="bg-stone-50 font-medium">
                  <td className="px-4 py-3" colSpan={2}>
                    Total / end of month
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <Money ore={incomeOre} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <Money ore={expenseOre} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <Money ore={monthEndBalance} />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
