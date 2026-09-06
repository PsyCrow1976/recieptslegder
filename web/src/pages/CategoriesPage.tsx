import { FormEvent, useEffect, useState } from "react";
import { api, type Category } from "../api";
import { useAuth } from "../auth";
import { ColorField, EmptyState, Field, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";
import { COLORS } from "../money";

export default function CategoriesPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [color, setColor] = useState(COLORS[0]);
  const [notes, setNotes] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState("");

  function reload() {
    api.categories(token!).then(setRows).catch((err: Error) => setError(err.message));
  }
  useEffect(reload, [token]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const payload = { name, color, notes: notes || undefined };
    try {
      if (editing) await api.updateCategory(token!, editing, payload);
      else await api.createCategory(token!, payload);
      setName("");
      setNotes("");
      setEditing(null);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function startEdit(row: Category) {
    setEditing(row.id);
    setName(row.name);
    setColor(row.color);
    setNotes(row.notes || "");
  }

  async function remove(id: string) {
    if (!confirm("Delete this category?")) return;
    try {
      await api.deleteCategory(token!, id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <PageHeader title="Categories" subtitle="Optional tags on an entry — groceries, salary, daughter, Sommerhus, investments." />
      <form onSubmit={onSubmit} className={`${cardClass} mb-6 grid gap-4 sm:grid-cols-2`}>
        <Field label="Name">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required />
        </Field>
        <Field label="Notes">
          <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </Field>
        <Field label="Color">
          <ColorField value={color} onChange={setColor} />
        </Field>
        <div className="flex items-end gap-2">
          <button className={btnPrimary} type="submit">
            {editing ? "Save category" : "Add category"}
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
        <EmptyState title="No categories yet" body="You can add entries without categories. Create some when you want to group spend or income." />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {rows.map((row) => (
            <li key={row.id} className={`${cardClass} flex items-start justify-between gap-3`}>
              <div className="flex items-center gap-3">
                <span className="h-8 w-8 rounded-full" style={{ backgroundColor: row.color }} />
                <p className="font-semibold">{row.name}</p>
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
