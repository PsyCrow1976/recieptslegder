import { FormEvent, useEffect, useState } from "react";
import { api, Tag, TagSpend } from "../api";
import { useAuth } from "../auth";
import { formatDkk } from "../money";

const COLORS = ["#c2410c", "#2563eb", "#16a34a", "#9333ea", "#0f766e", "#b45309", "#be123c"];

export default function TagsPage() {
  const { token } = useAuth();
  const [tags, setTags] = useState<Tag[]>([]);
  const [spend, setSpend] = useState<Record<string, TagSpend>>({});
  const [name, setName] = useState("");
  const [color, setColor] = useState(COLORS[0]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Tag | null>(null);

  async function reload() {
    if (!token) return;
    const list = await api.tags(token);
    setTags(list);
    const rows = await Promise.all(list.map((tag) => api.tagSpend(token, tag.id)));
    const next: Record<string, TagSpend> = {};
    for (const row of rows) next[row.tag.id] = row;
    setSpend(next);
  }

  useEffect(() => {
    reload().catch((err: Error) => setError(err.message));
  }, [token]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token || !name.trim()) return;
    setError("");
    try {
      await api.createTag(token, { name: name.trim(), color, notes: notes.trim() || undefined });
      setName("");
      setNotes("");
      await reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleSaveEdit(event: FormEvent) {
    event.preventDefault();
    if (!token || !editing) return;
    try {
      await api.updateTag(token, editing.id, {
        name: editing.name,
        color: editing.color,
        notes: editing.notes,
      });
      setEditing(null);
      await reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleDelete(tag: Tag) {
    if (!token) return;
    if (!confirm(`Delete tag “${tag.name}”? Receipts stay; the tag is removed from them.`)) return;
    await api.deleteTag(token, tag.id);
    await reload();
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Tags</h2>
        <p className="text-stone-500">Projects and groups. Attach several tags to a receipt for a full spend overview.</p>
      </div>

      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <form onSubmit={handleCreate} className="rounded-2xl border border-stone-200 bg-white p-4 space-y-3">
        <h3 className="font-semibold">New tag</h3>
        <div className="grid gap-3 sm:grid-cols-3">
          <input
            className="rounded-lg border border-stone-300 px-3 py-2"
            placeholder="Name (e.g. Sommerhus, Malerarbejde)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="rounded-lg border border-stone-300 px-3 py-2"
            placeholder="Notes (optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="flex items-center gap-2">
            {COLORS.map((swatch) => (
              <button
                type="button"
                key={swatch}
                onClick={() => setColor(swatch)}
                className={`h-8 w-8 rounded-full border-2 ${color === swatch ? "border-stone-900" : "border-transparent"}`}
                style={{ background: swatch }}
                aria-label={swatch}
              />
            ))}
            <button type="submit" className="ml-auto rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white">
              Create
            </button>
          </div>
        </div>
      </form>

      <ul className="space-y-3">
        {tags.map((tag) => (
          <li key={tag.id} className="rounded-2xl border border-stone-200 bg-white p-4">
            {editing?.id === tag.id ? (
              <form onSubmit={handleSaveEdit} className="space-y-3">
                <input
                  className="w-full rounded-lg border border-stone-300 px-3 py-2"
                  value={editing.name}
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                />
                <input
                  className="w-full rounded-lg border border-stone-300 px-3 py-2"
                  value={editing.notes ?? ""}
                  onChange={(e) => setEditing({ ...editing, notes: e.target.value })}
                />
                <div className="flex gap-2">
                  {COLORS.map((swatch) => (
                    <button
                      type="button"
                      key={swatch}
                      onClick={() => setEditing({ ...editing, color: swatch })}
                      className={`h-8 w-8 rounded-full border-2 ${editing.color === swatch ? "border-stone-900" : "border-transparent"}`}
                      style={{ background: swatch }}
                    />
                  ))}
                </div>
                <div className="flex gap-2">
                  <button type="submit" className="rounded-lg bg-brand-600 px-3 py-2 text-sm text-white">
                    Save
                  </button>
                  <button type="button" className="rounded-lg border px-3 py-2 text-sm" onClick={() => setEditing(null)}>
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="flex items-center gap-2 font-medium">
                    <span className="h-3 w-3 rounded-full" style={{ background: tag.color }} />
                    {tag.name}
                  </p>
                  {tag.notes && <p className="text-sm text-stone-500">{tag.notes}</p>}
                  <p className="text-sm text-stone-600">
                    {spend[tag.id]
                      ? `${formatDkk(spend[tag.id].total_ore)} across ${spend[tag.id].receipt_count} receipts`
                      : "—"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="rounded-lg border px-3 py-2 text-sm" onClick={() => setEditing(tag)}>
                    Edit
                  </button>
                  <button className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700" onClick={() => handleDelete(tag)}>
                    Delete
                  </button>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
