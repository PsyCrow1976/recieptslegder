import { FormEvent, useEffect, useState } from "react";
import { api, type Platform, type PlatformKind } from "../api";
import { useAuth } from "../auth";
import { ColorField, EmptyState, Field, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";
import { COLORS } from "../money";

const kinds: { value: PlatformKind; label: string }[] = [
  { value: "bank", label: "Bank" },
  { value: "investment", label: "Investment" },
  { value: "other", label: "Other" },
];

export default function PlatformsPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Platform[]>([]);
  const [name, setName] = useState("");
  const [kind, setKind] = useState<PlatformKind>("bank");
  const [website, setWebsite] = useState("");
  const [color, setColor] = useState(COLORS[1]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<string | null>(null);

  function reload() {
    api.platforms(token!).then(setRows).catch((err: Error) => setError(err.message));
  }
  useEffect(reload, [token]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const payload = { name, kind, website: website || undefined, color, notes: notes || undefined };
    try {
      if (editing) await api.updatePlatform(token!, editing, payload);
      else await api.createPlatform(token!, payload);
      setName("");
      setWebsite("");
      setNotes("");
      setEditing(null);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function startEdit(row: Platform) {
    setEditing(row.id);
    setName(row.name);
    setKind(row.kind);
    setWebsite(row.website || "");
    setColor(row.color);
    setNotes(row.notes || "");
  }

  async function remove(id: string) {
    if (!confirm("Delete this platform?")) return;
    try {
      await api.deletePlatform(token!, id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <PageHeader title="Platforms" subtitle="Banks and investment houses — for example Nordea and Nordnet. Accounts live under a platform." />
      <form onSubmit={onSubmit} className={`${cardClass} mb-6 grid gap-4 sm:grid-cols-2`}>
        <Field label="Name">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required placeholder="Nordea" />
        </Field>
        <Field label="Type">
          <select className={inputClass} value={kind} onChange={(e) => setKind(e.target.value as PlatformKind)}>
            {kinds.map((k) => (
              <option key={k.value} value={k.value}>
                {k.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Website">
          <input className={inputClass} value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://…" />
        </Field>
        <Field label="Notes">
          <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </Field>
        <Field label="Color">
          <ColorField value={color} onChange={setColor} />
        </Field>
        <div className="flex items-end gap-2">
          <button className={btnPrimary} type="submit">
            {editing ? "Save platform" : "Add platform"}
          </button>
          {editing && (
            <button type="button" className={btnGhost} onClick={() => setEditing(null)}>
              Cancel
            </button>
          )}
        </div>
        {error && <p className="sm:col-span-2 text-sm text-rose-700">{error}</p>}
      </form>

      {rows.length === 0 ? (
        <EmptyState title="No platforms yet" body="Add Nordea as a bank and Nordnet as an investment platform, then create the accounts that live on each." />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {rows.map((row) => (
            <li key={row.id} className={cardClass}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{row.name}</p>
                  <p className="text-sm capitalize text-stone-500">
                    {row.kind} · {row.account_count} account{row.account_count === 1 ? "" : "s"}
                  </p>
                  {row.website ? (
                    <a className="text-sm text-brand-700 hover:underline" href={row.website} target="_blank" rel="noreferrer">
                      {row.website}
                    </a>
                  ) : null}
                </div>
                <div className="flex gap-1">
                  <button className={btnGhost} type="button" onClick={() => startEdit(row)}>
                    Edit
                  </button>
                  <button className={btnGhost} type="button" onClick={() => remove(row.id)}>
                    Delete
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
