import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, Receipt, Tag } from "../api";
import { useAuth } from "../auth";
import { formatDateTime, formatDkk } from "../money";

export default function ReceiptsPage() {
  const { token } = useAuth();
  const [params, setParams] = useSearchParams();
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [error, setError] = useState("");
  const [q, setQ] = useState(params.get("q") ?? "");
  const tagId = params.get("tag") ?? "";
  const training = params.get("training") === "1";

  useEffect(() => {
    if (!token) return;
    api.tags(token).then(setTags).catch(() => undefined);
  }, [token]);

  useEffect(() => {
    if (!token) return;
    api
      .receipts(token, {
        tagId: tagId || undefined,
        q: params.get("q") || undefined,
        needsTraining: training || undefined,
        includeDrafts: training || undefined,
      })
      .then(setReceipts)
      .catch((err: Error) => setError(err.message));
  }, [token, tagId, params]);

  function search(event: FormEvent) {
    event.preventDefault();
    const next = new URLSearchParams(params);
    if (q) next.set("q", q);
    else next.delete("q");
    setParams(next);
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">{training ? "Training queue" : "Receipts"}</h2>
      {training && (
        <p className="text-sm text-amber-800">
          Slips local OCR could not fully read. Open one, correct the vendor and lines, then confirm. Keep them flagged
          if you want them as later training examples.
        </p>
      )}
      <form onSubmit={search} className="flex flex-col gap-2 sm:flex-row">
        <input
          className="flex-1 rounded-lg border border-stone-300 px-3 py-2"
          placeholder="Search vendor, SKU, description, invoice…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded-lg border border-stone-300 px-3 py-2"
          value={tagId}
          onChange={(e) => {
            const next = new URLSearchParams(params);
            if (e.target.value) next.set("tag", e.target.value);
            else next.delete("tag");
            setParams(next);
          }}
        >
          <option value="">All tags</option>
          {tags.map((tag) => (
            <option key={tag.id} value={tag.id}>
              {tag.name}
            </option>
          ))}
        </select>
        <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white">Search</button>
      </form>

      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {receipts.length === 0 ? (
        <p className="text-stone-500">No receipts yet.</p>
      ) : (
        <ul className="divide-y divide-stone-200 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {receipts.map((receipt) => (
            <li key={receipt.id}>
              <Link to={`/receipts/${receipt.id}`} className="flex flex-col gap-1 px-4 py-3 hover:bg-stone-50 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-medium">{receipt.vendor_name}</p>
                  <p className="text-sm text-stone-500">
                    {receipt.store_name ?? "—"} · {formatDateTime(receipt.purchased_at)}
                    {receipt.invoice_no ? ` · #${receipt.invoice_no}` : ""}
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {receipt.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="rounded-full px-2 py-0.5 text-xs text-white"
                        style={{ background: tag.color }}
                      >
                        {tag.name}
                      </span>
                    ))}
                    {receipt.needs_training && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">training</span>
                    )}
                    {receipt.status === "draft" && (
                      <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-600">draft</span>
                    )}
                    {!receipt.lines_sum_ok && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">total mismatch</span>
                    )}
                  </div>
                </div>
                <p className="font-semibold">{formatDkk(receipt.total_ore)}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
