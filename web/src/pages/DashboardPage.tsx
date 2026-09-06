import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Dashboard } from "../api";
import { useAuth } from "../auth";
import { Chip, EmptyState, Money, PageHeader, cardClass } from "../components/ui";
import { formatDate } from "../money";

export default function DashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard(token!).then(setData).catch((err: Error) => setError(err.message));
  }, [token]);

  if (error) return <p className="text-rose-700">{error}</p>;
  if (!data) return <p className="text-stone-500">Loading…</p>;

  const setup = [
    { done: data.people_count > 0, label: "Add people", to: "/people", hint: "You, your partner, her daughter" },
    { done: data.platform_count > 0, label: "Add platforms", to: "/platforms", hint: "Nordea, Nordnet, …" },
    { done: data.account_count > 0, label: "Add accounts", to: "/accounts", hint: "Assign one or more owners" },
    { done: data.movement_count > 0, label: "Record money in or out", to: "/entries/new", hint: "Attach a PDF or receipt if you have one" },
  ];
  const allEmpty = data.account_count === 0 && data.movement_count === 0;

  return (
    <div>
      <PageHeader
        title="Home"
        subtitle="Household balances across banks and investments."
        action={
          data.account_count > 0 ? (
            <Link to="/entries/new" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
              New entry
            </Link>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Household</p>
          <p className="mt-2 text-2xl">
            <Money ore={data.household_balance_ore} className="text-2xl" />
          </p>
        </div>
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">In this month</p>
          <p className="mt-2 text-2xl">
            <Money ore={data.this_month_in_ore} className="text-2xl" />
          </p>
        </div>
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Out this month</p>
          <p className="mt-2 text-2xl">
            <Money ore={-data.this_month_out_ore} className="text-2xl" />
          </p>
        </div>
      </div>

      {allEmpty && (
        <div className="mt-6">
          <EmptyState
            title="Nothing here yet"
            body="This is an empty household ledger. Add the people in the household, then Nordea / Nordnet (or any other platform), then the accounts, then money going in or out."
          />
        </div>
      )}

      <section className="mt-8">
        <h2 className="text-lg text-ink">Get started</h2>
        <ol className="mt-3 grid gap-3 sm:grid-cols-2">
          {setup.map((step, index) => (
            <li key={step.to} className={`${cardClass} flex items-start gap-3`}>
              <span
                className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  step.done ? "bg-brand-600 text-white" : "bg-stone-200 text-stone-600"
                }`}
              >
                {step.done ? "✓" : index + 1}
              </span>
              <div>
                <Link to={step.to} className="font-semibold text-brand-700 hover:underline">
                  {step.label}
                </Link>
                <p className="text-sm text-stone-500">{step.hint}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {data.accounts.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg text-ink">Accounts</h2>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {data.accounts.map((account) => (
              <Link key={account.id} to={`/accounts/${account.id}`} className={`${cardClass} hover:border-brand-600`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">{account.name}</p>
                    <p className="text-sm text-stone-500">
                      {account.platform.name} · {account.platform.kind}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {account.owners.map((owner) => (
                        <Chip key={owner.id} label={owner.name} color={owner.color} />
                      ))}
                    </div>
                  </div>
                  <Money ore={account.balance_ore} />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {data.by_person.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg text-ink">By person</h2>
          <p className="mt-1 text-sm text-stone-500">Shared accounts are listed separately and counted in full on each owner.</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            {data.by_person.map((row) => (
              <div key={row.person.id} className={cardClass}>
                <Chip label={row.person.name} color={row.person.color} />
                <p className="mt-3 text-sm text-stone-500">Own accounts</p>
                <Money ore={row.sole_balance_ore} />
                <p className="mt-2 text-sm text-stone-500">Shared accounts</p>
                <Money ore={row.shared_balance_ore} />
              </div>
            ))}
          </div>
        </section>
      )}

      {data.recent.length > 0 && (
        <section className="mt-8">
          <div className="flex items-baseline justify-between">
            <h2 className="text-lg text-ink">Recent entries</h2>
            <Link to="/entries" className="text-sm text-brand-700 hover:underline">
              All entries
            </Link>
          </div>
          <div className="mt-3 overflow-hidden rounded-2xl border border-stone-200 bg-white">
            {data.recent.map((m) => (
              <Link
                key={m.id}
                to={`/entries/${m.id}`}
                className="flex items-center justify-between gap-4 border-b border-stone-100 px-4 py-3 last:border-b-0 hover:bg-stone-50"
              >
                <div>
                  <p className="font-medium">{m.description || m.vendor?.name || "Entry"}</p>
                  <p className="text-xs text-stone-500">
                    {formatDate(m.posted_on)} · {m.account.name}
                  </p>
                </div>
                <Money ore={m.amount_ore} />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
