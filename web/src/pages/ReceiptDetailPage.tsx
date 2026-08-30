import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, LineWrite, Receipt, Tag, receiptImageObjectUrl } from "../api";
import { useAuth } from "../auth";
import { formatDateTime, formatDkk, parseDkkInput } from "../money";

type DraftLine = {
  item_number: string;
  quantity: string;
  description: string;
  line_total: string;
};

export default function ReceiptDetailPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [lookingUp, setLookingUp] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [total, setTotal] = useState("");
  const [vat, setVat] = useState("");
  const [notes, setNotes] = useState("");
  const [vendorName, setVendorName] = useState("");
  const [storeName, setStoreName] = useState("");
  const [invoiceNo, setInvoiceNo] = useState("");
  const [flagTraining, setFlagTraining] = useState(false);

  useEffect(() => {
    if (!token || !id) return;
    api.tags(token).then(setTags).catch(() => undefined);
    api
      .receipt(token, id)
      .then((data) => {
        setReceipt(data);
        hydrate(data);
      })
      .catch((err: Error) => setError(err.message));
    receiptImageObjectUrl(token, id)
      .then(setImageUrl)
      .catch(() => setImageUrl(null));
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, id]);

  function hydrate(data: Receipt) {
    setSelectedTags(data.tags.map((tag) => tag.id));
    setLines(
      data.lines.map((line) => ({
        item_number: line.item_number ?? "",
        quantity: String(line.quantity),
        description: line.description,
        line_total: (line.line_total_ore / 100).toFixed(2).replace(".", ","),
      })),
    );
    setTotal((data.total_ore / 100).toFixed(2).replace(".", ","));
    setVat((data.vat_ore / 100).toFixed(2).replace(".", ","));
    setNotes(data.notes ?? "");
    setVendorName(data.vendor_name);
    setStoreName(data.store_name ?? "");
    setInvoiceNo(data.invoice_no ?? "");
    setFlagTraining(data.needs_training);
  }

  const lineWrites: LineWrite[] = useMemo(
    () =>
      lines.map((line) => ({
        item_number: line.item_number.trim() || null,
        quantity: Number(line.quantity) || 1,
        description: line.description,
        line_total_ore: parseDkkInput(line.line_total),
      })),
    [lines],
  );

  async function save(event: FormEvent, status?: string) {
    event.preventDefault();
    if (!token || !id) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api.updateReceipt(token, id, {
        vendor_name: vendorName,
        store_name: storeName || null,
        invoice_no: invoiceNo || null,
        total_ore: parseDkkInput(total),
        vat_ore: parseDkkInput(vat),
        notes: notes || null,
        status: status ?? receipt?.status,
        needs_training: flagTraining,
        tag_ids: selectedTags,
        lines: lineWrites,
      });
      setReceipt(updated);
      hydrate(updated);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function lookup() {
    if (!token || !id) return;
    setLookingUp(true);
    setError("");
    try {
      const updated = await api.lookupProducts(token, id);
      setReceipt(updated);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLookingUp(false);
    }
  }

  async function remove() {
    if (!token || !id) return;
    if (!confirm("Delete this receipt?")) return;
    await api.deleteReceipt(token, id);
    navigate("/receipts");
  }

  if (!receipt) {
    return error ? <p className="text-red-700">{error}</p> : <p>Loading…</p>;
  }

  return (
    <form onSubmit={(e) => save(e)} className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm text-stone-500">
            <Link to="/receipts" className="text-brand-700 hover:underline">
              Receipts
            </Link>
          </p>
          <h2 className="text-2xl font-bold">{vendorName || receipt.vendor_name}</h2>
          <p className="text-stone-500">
            {storeName || receipt.store_name || "—"} · {formatDateTime(receipt.purchased_at)}
            {invoiceNo ? ` · invoice ${invoiceNo}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {receipt.status === "draft" && (
            <button
              type="button"
              disabled={saving}
              onClick={(e) => save(e, "saved")}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white"
            >
              {saving ? "Saving…" : "Confirm and save"}
            </button>
          )}
          {receipt.status === "saved" && (
            <button type="submit" disabled={saving} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white">
              {saving ? "Saving…" : "Save changes"}
            </button>
          )}
          <button type="button" onClick={lookup} disabled={lookingUp} className="rounded-lg border px-4 py-2 text-sm">
            {lookingUp ? "Looking up…" : "Match products"}
          </button>
          <button type="button" onClick={remove} className="rounded-lg border border-red-200 px-4 py-2 text-sm text-red-700">
            Delete
          </button>
        </div>
      </div>

      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {receipt.needs_training && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
          <p className="font-medium">Flagged for training</p>
          <p className="mt-1">
            Local OCR could not fully read this slip. Correct vendor and line items below, then confirm. The original
            photo and OCR text stay stored so we can teach new vendor layouts later.
          </p>
          <label className="mt-2 flex items-center gap-2">
            <input type="checkbox" checked={flagTraining} onChange={(e) => setFlagTraining(e.target.checked)} />
            Keep flagged in the training queue
          </label>
        </div>
      )}

      {receipt.warnings.length > 0 && (
        <ul className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
          {receipt.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-stone-200 bg-white p-3">
          {imageUrl ? (
            <img src={imageUrl} alt="Original receipt" className="mx-auto max-h-[70vh] object-contain" />
          ) : (
            <p className="p-6 text-center text-sm text-stone-500">No photo stored</p>
          )}
        </div>

        <div className="space-y-4">
          <section className="rounded-2xl border border-stone-200 bg-white p-4 space-y-3">
            <h3 className="font-semibold">Vendor</h3>
            <label className="block text-sm">
              Name
              <input
                className="mt-1 w-full rounded border px-2 py-1"
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              Store
              <input
                className="mt-1 w-full rounded border px-2 py-1"
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              Invoice
              <input
                className="mt-1 w-full rounded border px-2 py-1"
                value={invoiceNo}
                onChange={(e) => setInvoiceNo(e.target.value)}
              />
            </label>
            <p className="text-xs text-stone-500">
              Payment: {receipt.payment_method ?? "—"} · Kasse {receipt.register_no ?? "—"} · Cashier{" "}
              {receipt.cashier ?? "—"}
            </p>
          </section>
          <section className="rounded-2xl border border-stone-200 bg-white p-4">
            <h3 className="font-semibold">Tags</h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {tags.length === 0 && (
                <p className="text-sm text-stone-500">
                  Create tags on the <Link to="/tags" className="text-brand-700 underline">Tags</Link> page.
                </p>
              )}
              {tags.map((tag) => {
                const on = selectedTags.includes(tag.id);
                return (
                  <button
                    type="button"
                    key={tag.id}
                    onClick={() =>
                      setSelectedTags((current) =>
                        on ? current.filter((item) => item !== tag.id) : [...current, tag.id],
                      )
                    }
                    className={`rounded-full px-3 py-1 text-sm ${on ? "text-white" : "border text-stone-700"}`}
                    style={on ? { background: tag.color } : undefined}
                  >
                    {tag.name}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="overflow-x-auto rounded-2xl border border-stone-200 bg-white p-4">
            <h3 className="font-semibold">Line items</h3>
            <table className="mt-2 w-full min-w-[32rem] text-left text-sm">
              <thead>
                <tr className="text-stone-500">
                  <th className="py-1 pr-2">Varenr</th>
                  <th className="py-1 pr-2">Qty</th>
                  <th className="py-1 pr-2">Description</th>
                  <th className="py-1 pr-2 text-right">Ialt</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {lines.map((line, index) => {
                  const product = receipt.lines[index]?.product;
                  return (
                    <tr key={index} className="border-t align-top">
                      <td className="py-1 pr-2">
                        <input
                          className="w-20 rounded border px-1 py-1"
                          value={line.item_number}
                          onChange={(e) =>
                            setLines((current) =>
                              current.map((item, i) => (i === index ? { ...item, item_number: e.target.value } : item)),
                            )
                          }
                        />
                      </td>
                      <td className="py-1 pr-2">
                        <input
                          className="w-12 rounded border px-1 py-1"
                          value={line.quantity}
                          onChange={(e) =>
                            setLines((current) =>
                              current.map((item, i) => (i === index ? { ...item, quantity: e.target.value } : item)),
                            )
                          }
                        />
                      </td>
                      <td className="py-1 pr-2">
                        <input
                          className="w-full rounded border px-1 py-1"
                          value={line.description}
                          onChange={(e) =>
                            setLines((current) =>
                              current.map((item, i) => (i === index ? { ...item, description: e.target.value } : item)),
                            )
                          }
                        />
                        {product?.url && (
                          <a
                            href={product.url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-0.5 block text-xs text-brand-700 hover:underline"
                          >
                            {product.title ?? "Open on harald-nyborg.dk"}
                            {product.last_web_price_ore != null
                              ? ` · web ${formatDkk(product.last_web_price_ore)}`
                              : ""}
                          </a>
                        )}
                      </td>
                      <td className="py-1 pr-2">
                        <input
                          className="w-24 rounded border px-1 py-1 text-right"
                          value={line.line_total}
                          onChange={(e) =>
                            setLines((current) =>
                              current.map((item, i) => (i === index ? { ...item, line_total: e.target.value } : item)),
                            )
                          }
                        />
                      </td>
                      <td className="py-1">
                        <button
                          type="button"
                          className="text-xs text-red-700"
                          onClick={() => setLines((current) => current.filter((_, i) => i !== index))}
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <button
              type="button"
              className="mt-2 text-sm text-brand-700"
              onClick={() =>
                setLines((current) => [...current, { item_number: "", quantity: "1", description: "", line_total: "0,00" }])
              }
            >
              Add line
            </button>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <label>
                Total
                <input className="mt-1 w-full rounded border px-2 py-1" value={total} onChange={(e) => setTotal(e.target.value)} />
              </label>
              <label>
                Moms
                <input className="mt-1 w-full rounded border px-2 py-1" value={vat} onChange={(e) => setVat(e.target.value)} />
              </label>
            </div>
            <p className="mt-2 text-xs text-stone-500">
              Payment: {receipt.payment_method ?? "—"} · Kasse {receipt.register_no ?? "—"} · Cashier {receipt.cashier ?? "—"}
            </p>
            <label className="mt-2 block text-sm">
              Notes
              <textarea
                className="mt-1 w-full rounded border px-2 py-1"
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </label>
          </section>
        </div>
      </div>
    </form>
  );
}
