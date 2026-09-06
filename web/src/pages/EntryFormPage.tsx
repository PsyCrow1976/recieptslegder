import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  api,
  attachmentObjectUrl,
  type AccountSummary,
  type Attachment,
  type Category,
  type Movement,
  type Vendor,
} from "../api";
import { useAuth } from "../auth";
import { Field, Money, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";
import { formatDkk, parseDkkInput, todayIso } from "../money";

type DraftItem = {
  key: string;
  description: string;
  vendor_name: string;
  product_url: string;
  amount: string;
  quantity: string;
};

function newItem(): DraftItem {
  return { key: crypto.randomUUID(), description: "", vendor_name: "", product_url: "", amount: "", quantity: "1" };
}

export default function EntryFormPage() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loaded, setLoaded] = useState(!isEdit);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const [accountId, setAccountId] = useState(params.get("account") || "");
  const [postedOn, setPostedOn] = useState(todayIso());
  const [direction, setDirection] = useState<"in" | "out">("out");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [vendorName, setVendorName] = useState("");
  const [categoryIds, setCategoryIds] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<DraftItem[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [existingFiles, setExistingFiles] = useState<Attachment[]>([]);
  const [preview, setPreview] = useState<{ url: string; type: string; name: string } | null>(null);

  useEffect(() => {
    const presetAccount = params.get("account") || "";
    Promise.all([api.accounts(token!), api.vendors(token!), api.categories(token!)]).then(([a, v, c]) => {
      setAccounts(a);
      setVendors(v);
      setCategories(c);
      if (!isEdit && !presetAccount && a[0]) setAccountId(a[0].id);
    });
  }, [token, isEdit, params]);

  useEffect(() => {
    if (!id) return;
    api
      .movement(token!, id)
      .then((m: Movement) => {
        setAccountId(m.account_id);
        setPostedOn(m.posted_on);
        setDirection(m.amount_ore < 0 ? "out" : "in");
        setAmount(formatDkk(Math.abs(m.amount_ore)).replace(" kr", ""));
        setDescription(m.description);
        setVendorName(m.vendor?.name || "");
        setCategoryIds(m.categories.map((c) => c.id));
        setNotes(m.notes || "");
        setExistingFiles(m.attachments);
        setItems(
          m.items.map((item) => ({
            key: item.id,
            description: item.description,
            vendor_name: item.vendor?.name || "",
            product_url: item.product_url || "",
            amount: formatDkk(item.amount_ore).replace(" kr", ""),
            quantity: String(item.quantity),
          })),
        );
        setLoaded(true);
      })
      .catch((err: Error) => setError(err.message));
  }, [id, token]);

  const itemsSum = useMemo(
    () => items.reduce((sum, item) => sum + parseDkkInput(item.amount), 0),
    [items],
  );
  const headerAmount = parseDkkInput(amount);
  const signedAmount = items.length > 0 ? itemsSum : direction === "in" ? Math.abs(headerAmount) : -Math.abs(headerAmount);

  function toggleCategory(catId: string) {
    setCategoryIds((current) => (current.includes(catId) ? current.filter((x) => x !== catId) : [...current, catId]));
  }

  function updateItem(key: string, patch: Partial<DraftItem>) {
    setItems((current) => current.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  }

  async function openFile(attachment: Attachment) {
    if (!id) return;
    const url = await attachmentObjectUrl(token!, id, attachment.id);
    setPreview({ url, type: attachment.content_type, name: attachment.original_filename });
  }

  async function removeExisting(attachment: Attachment) {
    if (!id) return;
    const updated = await api.deleteAttachment(token!, id, attachment.id);
    setExistingFiles(updated.attachments);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        account_id: accountId,
        posted_on: postedOn,
        amount_ore: signedAmount,
        description,
        vendor_name: vendorName || null,
        category_ids: categoryIds,
        notes: notes || null,
        items: items.map((item) => ({
          description: item.description,
          vendor_name: item.vendor_name || null,
          product_url: item.product_url || null,
          amount_ore: parseDkkInput(item.amount),
          quantity: Number(item.quantity) || 1,
        })),
      };
      const saved = isEdit ? await api.updateMovement(token!, id!, payload) : await api.createMovement(token!, payload);
      if (files.length) {
        await api.uploadAttachments(token!, saved.id, files);
      }
      navigate(`/accounts/${saved.account_id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function removeEntry() {
    if (!id || !confirm("Delete this entry and its files?")) return;
    await api.deleteMovement(token!, id);
    navigate("/entries");
  }

  if (!loaded) return <p className="text-stone-500">Loading…</p>;
  if (accounts.length === 0) {
    return (
      <div>
        <PageHeader title="New entry" />
        <p className="text-stone-500">
          Create an account first. <Link to="/accounts" className="text-brand-700 hover:underline">Accounts</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={isEdit ? "Edit entry" : "New entry"}
        subtitle="Money in or out of one account. Attach a PDF or receipt, then optionally split into items."
        action={
          isEdit ? (
            <button type="button" className={btnGhost} onClick={removeEntry}>
              Delete
            </button>
          ) : null
        }
      />

      <form onSubmit={onSubmit} className="grid gap-6">
        <section className={`${cardClass} grid gap-4 sm:grid-cols-2`}>
          <Field label="Account">
            <select className={inputClass} value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} · {a.platform.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Date">
            <input type="date" className={inputClass} value={postedOn} onChange={(e) => setPostedOn(e.target.value)} required />
          </Field>
          <div>
            <p className="text-sm font-medium text-stone-700">Direction</p>
            <div className="mt-1 flex gap-2">
              {(["in", "out"] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setDirection(value)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                    direction === value
                      ? value === "in"
                        ? "bg-emerald-700 text-white"
                        : "bg-rose-700 text-white"
                      : "bg-stone-100 text-stone-700"
                  }`}
                >
                  {value === "in" ? "Money in" : "Money out"}
                </button>
              ))}
            </div>
          </div>
          <Field label="Amount">
            <input
              className={inputClass}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0,00"
              disabled={items.length > 0}
            />
            {items.length > 0 ? (
              <p className="mt-1 text-xs text-stone-500">Amount is the sum of line items.</p>
            ) : null}
          </Field>
          <Field label="Description">
            <input className={inputClass} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Salary, Netto, Nordnet buy…" />
          </Field>
          <Field label="Vendor">
            <input
              className={inputClass}
              list="vendor-list"
              value={vendorName}
              onChange={(e) => setVendorName(e.target.value)}
              placeholder="Netto, Nordea, employer…"
            />
            <datalist id="vendor-list">
              {vendors.map((v) => (
                <option key={v.id} value={v.name} />
              ))}
            </datalist>
          </Field>
          <div className="sm:col-span-2">
            <p className="text-sm font-medium text-stone-700">Categories (optional, one or more)</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {categories.length === 0 && <p className="text-sm text-stone-500">Add categories under Categories if you want them.</p>}
              {categories.map((c) => (
                <button
                  type="button"
                  key={c.id}
                  onClick={() => toggleCategory(c.id)}
                  className={`rounded-full px-3 py-1 text-sm ${
                    categoryIds.includes(c.id) ? "bg-brand-600 text-white" : "bg-stone-100 text-stone-700"
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>
          </div>
          <Field label="Notes">
            <textarea className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
          </Field>
        </section>

        <section className={cardClass}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg text-ink">Line items</h2>
              <p className="text-sm text-stone-500">Optional. Each item has its own vendor, product link, and amount (positive or negative).</p>
            </div>
            <button type="button" className={btnGhost} onClick={() => setItems((current) => [...current, newItem()])}>
              Add item
            </button>
          </div>
          {items.length > 0 && (
            <div className="mt-4 space-y-4">
              {items.map((item, index) => (
                <div key={item.key} className="grid gap-3 rounded-xl border border-stone-200 p-3 sm:grid-cols-2">
                  <Field label={`Item ${index + 1}`}>
                    <input className={inputClass} value={item.description} onChange={(e) => updateItem(item.key, { description: e.target.value })} placeholder="Product name" />
                  </Field>
                  <Field label="Vendor">
                    <input className={inputClass} list="vendor-list" value={item.vendor_name} onChange={(e) => updateItem(item.key, { vendor_name: e.target.value })} />
                  </Field>
                  <Field label="Product page">
                    <input className={inputClass} value={item.product_url} onChange={(e) => updateItem(item.key, { product_url: e.target.value })} placeholder="https://…" />
                  </Field>
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Amount (+ in / − out)">
                      <input className={inputClass} value={item.amount} onChange={(e) => updateItem(item.key, { amount: e.target.value })} placeholder="-129,95" />
                    </Field>
                    <Field label="Qty">
                      <input className={inputClass} value={item.quantity} onChange={(e) => updateItem(item.key, { quantity: e.target.value })} />
                    </Field>
                  </div>
                  <button type="button" className={`${btnGhost} sm:col-span-2 w-fit`} onClick={() => setItems((current) => current.filter((row) => row.key !== item.key))}>
                    Remove item
                  </button>
                </div>
              ))}
              <p className="text-sm">
                Items total: <Money ore={itemsSum} /> · Entry: <Money ore={signedAmount} />
              </p>
            </div>
          )}
        </section>

        <section className={cardClass}>
          <h2 className="text-lg text-ink">Documents</h2>
          <p className="text-sm text-stone-500">PDF statements, receipt photos, or other files for this amount.</p>
          <input
            className="mt-3 block w-full text-sm"
            type="file"
            multiple
            accept="image/*,.pdf,.txt,.csv,.doc,.docx,.xls,.xlsx"
            onChange={(e) => setFiles(Array.from(e.target.files || []))}
          />
          {files.length > 0 && (
            <ul className="mt-2 text-sm text-stone-600">
              {files.map((file) => (
                <li key={file.name}>{file.name}</li>
              ))}
            </ul>
          )}
          {existingFiles.length > 0 && (
            <ul className="mt-4 space-y-2">
              {existingFiles.map((file) => (
                <li key={file.id} className="flex items-center justify-between gap-3 rounded-lg bg-stone-50 px-3 py-2 text-sm">
                  <button type="button" className="text-left text-brand-700 hover:underline" onClick={() => openFile(file)}>
                    {file.original_filename}
                  </button>
                  <button type="button" className={btnGhost} onClick={() => removeExisting(file)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {error && <p className="text-sm text-rose-700">{error}</p>}

        <div className="flex items-center gap-3">
          <button className={btnPrimary} disabled={saving} type="submit">
            {saving ? "Saving…" : isEdit ? "Save entry" : "Create entry"}
          </button>
          <span className="text-sm text-stone-500">
            Will record <Money ore={signedAmount} /> on the selected account.
          </span>
        </div>
      </form>

      {preview && (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/60 p-4" onClick={() => setPreview(null)}>
          <div className="max-h-[90vh] max-w-4xl overflow-auto rounded-xl bg-white p-4" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <p className="font-medium">{preview.name}</p>
              <button type="button" className={btnGhost} onClick={() => setPreview(null)}>
                Close
              </button>
            </div>
            {preview.type.startsWith("image/") ? (
              <img src={preview.url} alt={preview.name} className="max-h-[80vh]" />
            ) : preview.type === "application/pdf" ? (
              <iframe title={preview.name} src={preview.url} className="h-[80vh] w-[70vw]" />
            ) : (
              <a href={preview.url} className="text-brand-700" download={preview.name}>
                Download
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
