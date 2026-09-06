import { FormEvent, useEffect, useState } from "react";
import { api, type Person } from "../api";
import { useAuth } from "../auth";
import { ColorField, EmptyState, Field, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";
import { COLORS } from "../money";

export default function PeoplePage() {
  const { token } = useAuth();
  const [people, setPeople] = useState<Person[]>([]);
  const [name, setName] = useState("");
  const [color, setColor] = useState(COLORS[0]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<string | null>(null);

  function reload() {
    api.people(token!).then(setPeople).catch((err: Error) => setError(err.message));
  }

  useEffect(reload, [token]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      if (editing) {
        await api.updatePerson(token!, editing, { name, color, notes: notes || null });
      } else {
        await api.createPerson(token!, { name, color, notes: notes || undefined });
      }
      setName("");
      setNotes("");
      setEditing(null);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function startEdit(person: Person) {
    setEditing(person.id);
    setName(person.name);
    setColor(person.color);
    setNotes(person.notes || "");
  }

  async function remove(id: string) {
    if (!confirm("Delete this person?")) return;
    try {
      await api.deletePerson(token!, id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <PageHeader title="People" subtitle="Household members who can own accounts — one person or several on a shared account." />
      <form onSubmit={onSubmit} className={`${cardClass} mb-6 grid gap-4 sm:grid-cols-2`}>
        <Field label="Name">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Christer" />
        </Field>
        <Field label="Notes">
          <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional" />
        </Field>
        <Field label="Color">
          <ColorField value={color} onChange={setColor} />
        </Field>
        <div className="flex items-end gap-2">
          <button className={btnPrimary} type="submit">
            {editing ? "Save person" : "Add person"}
          </button>
          {editing && (
            <button
              type="button"
              className={btnGhost}
              onClick={() => {
                setEditing(null);
                setName("");
                setNotes("");
              }}
            >
              Cancel
            </button>
          )}
        </div>
        {error && <p className="sm:col-span-2 text-sm text-rose-700">{error}</p>}
      </form>

      {people.length === 0 ? (
        <EmptyState title="No people yet" body="Add yourself, your girlfriend, and her daughter. You will pick them as owners when you create accounts." />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {people.map((person) => (
            <li key={person.id} className={cardClass}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="h-8 w-8 rounded-full" style={{ backgroundColor: person.color }} />
                  <div>
                    <p className="font-semibold">{person.name}</p>
                    {person.notes ? <p className="text-sm text-stone-500">{person.notes}</p> : null}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button className={btnGhost} type="button" onClick={() => startEdit(person)}>
                    Edit
                  </button>
                  <button className={btnGhost} type="button" onClick={() => remove(person.id)}>
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
