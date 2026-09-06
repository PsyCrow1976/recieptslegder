import { FormEvent, useEffect, useState } from "react";
import { api, type Vendor } from "../api";
import { useAuth } from "../auth";
import { EmptyState, Field, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";

export default function VendorsPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Vendor[]>([]);
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [notes, setNotes] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState("");

  function reload() {
    api.vendors(token!).then(setRows).catch((err: Error) => setError(err.message));
  }
  useEffect(reload, [token]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const payload = { name, website: website || undefined, notes: notes || undefined };
    try {
      if (editing) await api.updateVendor(token!, editing, payload);
      else await api.createVendor(token!, payload);
      setName("");
      setWebsite("");
      setNotes("");
      setEditing(null);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function startEdit(row: Vendor) {
    setEditing(row.id);
    setName(row.name);
    setWebsite(row.website || "");
    setNotes(row.notes || "");
  }

  async function remove(id: string) {
    if (!confirm("Delete this vendor?")) return;
    try {
      await api.deleteVendor(token!, id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <PageHeader title="Vendors" subtitle="Shops, employers, banks, or anyone money comes from or goes to. You can also type a new vendor name on an entry." />
      <form onSubmit={onSubmit} className={`${cardClass} mb-6 grid gap-4 sm:grid-cols-2`}>
        <Field label="Name">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required />
        </Field>
        <Field label="Website">
          <input className={inputClass} value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://…" />
        </Field>
        <Field label="Notes">
          <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </Field>
        <div className="flex items-end gap-2">
          <button className={btnPrimary} type="submit">
            {editing ? "Save vendor" : "Add vendor"}
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
        <EmptyState title="No vendors yet" body="Vendors are created here or automatically when you type a name on an entry or line item." />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {rows.map((row) => (
            <li key={row.id} className={`${cardClass} flex items-start justify-between gap-3`}>
              <div>
                <p className="font-semibold">{row.name}</p>
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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
