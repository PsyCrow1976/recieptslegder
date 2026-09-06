import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Person, type Platform } from "../api";
import { useAuth } from "../auth";
import { Chip, EmptyState, Field, Money, PageHeader, btnPrimary, cardClass, inputClass } from "../components/ui";
import { parseDkkInput } from "../money";

export default function AccountsPage() {
  const { token } = useAuth();
  const [accounts, setAccounts] = useState<Awaited<ReturnType<typeof api.accounts>>>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [name, setName] = useState("");
  const [platformId, setPlatformId] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [currency, setCurrency] = useState("DKK");
  const [opening, setOpening] = useState("0");
  const [ownerIds, setOwnerIds] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  function reload() {
    Promise.all([api.accounts(token!), api.people(token!), api.platforms(token!)])
      .then(([a, p, pl]) => {
        setAccounts(a);
        setPeople(p);
        setPlatforms(pl);
        if (!platformId && pl[0]) setPlatformId(pl[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }
  useEffect(reload, [token]);

  function toggleOwner(id: string) {
    setOwnerIds((current) => (current.includes(id) ? current.filter((x) => x !== id) : [...current, id]));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.createAccount(token!, {
        platform_id: platformId,
        name,
        account_number: accountNumber || undefined,
        currency,
        opening_balance_ore: parseDkkInput(opening),
        owner_ids: ownerIds,
        notes: notes || undefined,
      });
      setName("");
      setAccountNumber("");
      setOpening("0");
      setNotes("");
      setOwnerIds([]);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const canCreate = people.length > 0 && platforms.length > 0;

  return (
    <div>
      <PageHeader title="Accounts" subtitle="A bank account or investment depot on a platform, with one owner or several for shared accounts." />

      {!canCreate && (
        <div className="mb-6">
          <EmptyState
            title="Add people and platforms first"
            body="An account needs a platform (Nordea, Nordnet, …) and at least one owner."
            to={people.length === 0 ? "/people" : "/platforms"}
            cta={people.length === 0 ? "Add people" : "Add platforms"}
          />
        </div>
      )}

      {canCreate && (
        <form onSubmit={onSubmit} className={`${cardClass} mb-6 grid gap-4 sm:grid-cols-2`}>
          <Field label="Account name">
            <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required placeholder="Lønkonto / Aktiedepot" />
          </Field>
          <Field label="Platform">
            <select className={inputClass} value={platformId} onChange={(e) => setPlatformId(e.target.value)} required>
              {platforms.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.kind})
                </option>
              ))}
            </select>
          </Field>
          <Field label="Account number (optional)">
            <input className={inputClass} value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} />
          </Field>
          <Field label="Currency">
            <input className={inputClass} value={currency} onChange={(e) => setCurrency(e.target.value.toUpperCase())} maxLength={3} />
          </Field>
          <Field label="Opening balance">
            <input className={inputClass} value={opening} onChange={(e) => setOpening(e.target.value)} />
          </Field>
          <Field label="Notes">
            <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </Field>
          <div className="sm:col-span-2">
            <p className="text-sm font-medium text-stone-700">Owners</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {people.map((person) => (
                <button
                  type="button"
                  key={person.id}
                  onClick={() => toggleOwner(person.id)}
                  className={`rounded-full px-3 py-1 text-sm ${
                    ownerIds.includes(person.id) ? "bg-brand-600 text-white" : "bg-stone-100 text-stone-700"
                  }`}
                >
                  {person.name}
                </button>
              ))}
            </div>
            <p className="mt-1 text-xs text-stone-500">Select one person, or several if the account is shared.</p>
          </div>
          <div>
            <button className={btnPrimary} type="submit">
              Add account
            </button>
          </div>
          {error && <p className="sm:col-span-2 text-sm text-rose-700">{error}</p>}
        </form>
      )}

      {accounts.length === 0 && canCreate ? (
        <EmptyState title="No accounts yet" body="Create the Nordea accounts and Nordnet depots, and assign owners." />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {accounts.map((account) => (
            <Link key={account.id} to={`/accounts/${account.id}`} className={`${cardClass} hover:border-brand-600`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{account.name}</p>
                  <p className="text-sm text-stone-500">
                    {account.platform.name} · {account.currency}
                    {account.account_number ? ` · ${account.account_number}` : ""}
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
      )}
    </div>
  );
}
