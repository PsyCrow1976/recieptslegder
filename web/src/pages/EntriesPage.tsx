import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type AccountSummary, type Category, type Movement, type Person } from "../api";
import { useAuth } from "../auth";
import { Chip, EmptyState, Money, PageHeader, btnPrimary, inputClass } from "../components/ui";
import { formatDate } from "../money";

export default function EntriesPage() {
  const { token } = useAuth();
  const [params, setParams] = useSearchParams();
  const [rows, setRows] = useState<Movement[]>([]);
  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [q, setQ] = useState(params.get("q") || "");
  const [error, setError] = useState("");

  const accountId = params.get("account") || "";
  const personId = params.get("person") || "";
  const categoryId = params.get("category") || "";

  useEffect(() => {
    Promise.all([
      api.movements(token!, {
        accountId: accountId || undefined,
        personId: personId || undefined,
        categoryId: categoryId || undefined,
        q: q || undefined,
      }),
      api.accounts(token!),
      api.people(token!),
      api.categories(token!),
    ])
      .then(([m, a, p, c]) => {
        setRows(m);
        setAccounts(a);
        setPeople(p);
        setCategories(c);
      })
      .catch((err: Error) => setError(err.message));
  }, [token, accountId, personId, categoryId, q]);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  }

  return (
    <div>
      <PageHeader
        title="Entries"
        subtitle="Money going in or out of an account. Each entry can have a vendor, categories, line items, and documents."
        action={
          <div className="flex gap-2">
            <Link
              to="/entries/import"
              className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50"
            >
              Import CSV
            </Link>
            <Link to="/entries/new" className={btnPrimary}>
              New entry
            </Link>
          </div>
        }
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-4">
        <input className={inputClass} placeholder="Search description" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className={inputClass} value={accountId} onChange={(e) => setFilter("account", e.target.value)}>
          <option value="">All accounts</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
        <select className={inputClass} value={personId} onChange={(e) => setFilter("person", e.target.value)}>
          <option value="">All people</option>
          {people.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select className={inputClass} value={categoryId} onChange={(e) => setFilter("category", e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="text-sm text-rose-700">{error}</p>}

      {rows.length === 0 ? (
        <EmptyState
          title="No entries yet"
          body="When money hits a Nordea account or you buy something, record it here. Attach the PDF or receipt photo and split it into items if you want."
          to="/entries/new"
          cta="New entry"
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {rows.map((m) => (
            <Link
              key={m.id}
              to={`/entries/${m.id}`}
              className="flex flex-col gap-2 border-b border-stone-100 px-4 py-3 last:border-b-0 hover:bg-stone-50 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium">{m.description || m.vendor?.name || "Entry"}</p>
                <p className="text-xs text-stone-500">
                  {formatDate(m.posted_on)} · {m.account.name} · {m.account.platform_name}
                </p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.vendor ? <Chip label={m.vendor.name} /> : null}
                  {m.categories.map((c) => (
                    <Chip key={c.id} label={c.name} color={c.color} />
                  ))}
                </div>
              </div>
              <Money ore={m.amount_ore} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
