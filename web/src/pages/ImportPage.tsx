import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  type AccountSummary,
  type Category,
  type ImportPreview,
  type ImportPreviewRow,
  type Vendor,
} from "../api";
import { useAuth } from "../auth";
import { Field, Money, PageHeader, btnGhost, btnPrimary, cardClass, inputClass } from "../components/ui";
import { formatDate } from "../money";

type Draft = ImportPreviewRow & {
  include: boolean;
  vendorChoice: string;
  categoryChoice: string;
};

function vendorOption(row: Draft) {
  if (row.suggested_vendor_id) return `id:${row.suggested_vendor_id}`;
  if (row.suggested_vendor_name) return `new:${row.suggested_vendor_name}`;
  return "";
}

export default function ImportPage() {
  const { token } = useAuth();
  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accountId, setAccountId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [filter, setFilter] = useState<"all" | "new" | "duplicate" | "skipped">("all");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");

  useEffect(() => {
    Promise.all([api.accounts(token!), api.vendors(token!), api.categories(token!)]).then(([a, v, c]) => {
      setAccounts(a);
      setVendors(v);
      setCategories(c);
      if (a[0] && !accountId) setAccountId(a[0].id);
    });
  }, [token]);

  function toDrafts(rows: ImportPreviewRow[]): Draft[] {
    return rows.map((row) => ({
      ...row,
      include: row.status === "new",
      vendorChoice: vendorOption({ ...row, include: true, vendorChoice: "", categoryChoice: "" }),
      categoryChoice: row.suggested_category_id ? row.suggested_category_id : "",
    }));
  }

  async function onPreview(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setLoading(true);
    setError("");
    setResult("");
    try {
      const data = await api.previewImport(token!, file, accountId || undefined);
      setPreview(data);
      setDrafts(toDrafts(data.rows));
      if (!accountId && data.suggested_account_id) {
        setAccountId(data.suggested_account_id);
        const again = await api.previewImport(token!, file, data.suggested_account_id);
        setPreview(again);
        setDrafts(toDrafts(again.rows));
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const visible = useMemo(
    () => drafts.filter((row) => filter === "all" || row.status === filter),
    [drafts, filter],
  );
  const selectedNew = drafts.filter((row) => row.include && row.status === "new" && row.posted_on && row.amount_ore !== null);

  async function onCommit() {
    if (!accountId) {
      setError("Link the CSV to an account first.");
      return;
    }
    setLoading(true);
    setError("");
    setResult("");
    try {
      const payload = {
        account_id: accountId,
        rows: selectedNew.map((row) => {
          const vendorId = row.vendorChoice.startsWith("id:") ? row.vendorChoice.slice(3) : null;
          const vendorName = row.vendorChoice.startsWith("new:") ? row.vendorChoice.slice(4) : !row.vendorChoice ? row.suggested_vendor_name : null;
          return {
            import_key: row.import_key,
            posted_on: row.posted_on as string,
            amount_ore: row.amount_ore as number,
            description: row.label,
            vendor_id: vendorId,
            vendor_name: vendorId ? null : vendorName,
            category_ids: row.categoryChoice ? [row.categoryChoice] : [],
          };
        }),
      };
      const done = await api.commitImport(token!, payload);
      setResult(`Imported ${done.created} new entries. ${done.skipped_duplicate} already existed.`);
      if (file) {
        const again = await api.previewImport(token!, file, accountId);
        setPreview(again);
        setDrafts(toDrafts(again.rows));
      }
      const [v, c] = await Promise.all([api.vendors(token!), api.categories(token!)]);
      setVendors(v);
      setCategories(c);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function patch(importKey: string, update: Partial<Draft>) {
    setDrafts((current) => current.map((row) => (row.import_key === importKey ? { ...row, ...update } : row)));
  }

  const selectedAccount = accounts.find((a) => a.id === accountId);

  return (
    <div>
      <PageHeader
        title="Import CSV"
        subtitle="Nordea account export. Link it to an account, review new vs duplicate rows, then import."
        action={
          <Link to="/entries" className={btnGhost}>
            Back to entries
          </Link>
        }
      />

      <form onSubmit={onPreview} className={`${cardClass} mb-6 grid gap-4 sm:grid-cols-2`}>
        <Field label="Account">
          <select className={inputClass} value={accountId} onChange={(e) => setAccountId(e.target.value)}>
            <option value="">Select account…</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
                {account.account_number ? ` · ${account.account_number}` : ""}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-stone-500">
            Put the Nordea register and account on the account, e.g. 2112-9040298476, so the file can be matched.
          </p>
        </Field>
        <Field label="CSV file">
          <input
            className="block w-full text-sm"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </Field>
        <div className="sm:col-span-2">
          <button className={btnPrimary} type="submit" disabled={loading}>
            {loading ? "Reading…" : "Review file"}
          </button>
        </div>
        {error && <p className="sm:col-span-2 text-sm text-rose-700">{error}</p>}
        {result && <p className="sm:col-span-2 text-sm text-emerald-800">{result}</p>}
      </form>

      {preview && (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-4">
            <div className={cardClass}>
              <p className="text-xs uppercase tracking-wide text-stone-500">File</p>
              <p className="mt-1 font-medium">{preview.filename}</p>
              {preview.detected_account_number ? (
                <p className="text-xs text-stone-500">Nordea account {preview.detected_account_number}</p>
              ) : null}
              {selectedAccount ? <p className="text-xs text-stone-500">Linked to {selectedAccount.name}</p> : null}
            </div>
            <div className={cardClass}>
              <p className="text-xs uppercase tracking-wide text-stone-500">New</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-800">{preview.new_count}</p>
            </div>
            <div className={cardClass}>
              <p className="text-xs uppercase tracking-wide text-stone-500">Already in ledger</p>
              <p className="mt-1 text-2xl font-semibold text-amber-800">{preview.duplicate_count}</p>
            </div>
            <div className={cardClass}>
              <p className="text-xs uppercase tracking-wide text-stone-500">Skipped</p>
              <p className="mt-1 text-2xl font-semibold text-stone-600">{preview.skipped_count}</p>
            </div>
          </div>

          <div className="mb-3 flex flex-wrap items-center gap-2">
            {(["all", "new", "duplicate", "skipped"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setFilter(value)}
                className={`rounded-full px-3 py-1 text-sm ${filter === value ? "bg-brand-600 text-white" : "bg-stone-100 text-stone-700"}`}
              >
                {value === "all" ? `All ${preview.row_count}` : value}
              </button>
            ))}
            <button className={`${btnPrimary} ml-auto`} type="button" disabled={loading || selectedNew.length === 0} onClick={onCommit}>
              Import {selectedNew.length} new
            </button>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
                <tr>
                  <th className="px-3 py-2">Import</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Amount</th>
                  <th className="px-3 py-2">Text</th>
                  <th className="px-3 py-2">Vendor</th>
                  <th className="px-3 py-2">Category</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => (
                  <tr key={row.import_key} className={`border-t border-stone-100 ${row.status === "duplicate" ? "bg-amber-50/60" : row.status === "skipped" ? "bg-stone-50" : ""}`}>
                    <td className="px-3 py-2">
                      {row.status === "new" ? (
                        <input type="checkbox" checked={row.include} onChange={(e) => patch(row.import_key, { include: e.target.checked })} />
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {row.status === "new" && <span className="font-semibold text-emerald-800">New</span>}
                      {row.status === "duplicate" && (
                        <span className="font-semibold text-amber-800">
                          Duplicate
                          {row.existing_movement_id ? (
                            <>
                              {" "}
                              <Link className="underline" to={`/entries/${row.existing_movement_id}`}>
                                open
                              </Link>
                            </>
                          ) : null}
                        </span>
                      )}
                      {row.status === "skipped" && <span className="text-stone-500">{row.skip_reason}</span>}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">{formatDate(row.posted_on)}</td>
                    <td className="px-3 py-2 whitespace-nowrap">{row.amount_ore !== null ? <Money ore={row.amount_ore} /> : "—"}</td>
                    <td className="px-3 py-2">
                      <div className="font-medium">{row.label}</div>
                      {row.name && row.name !== row.label ? <div className="text-xs text-stone-500">{row.name}</div> : null}
                    </td>
                    <td className="px-3 py-2 min-w-[14rem]">
                      {row.status === "new" ? (
                        <>
                          <select
                            className={inputClass}
                            value={row.vendorChoice}
                            onChange={(e) => patch(row.import_key, { vendorChoice: e.target.value })}
                          >
                            <option value="">No vendor</option>
                            {row.suggested_vendor_name && !row.suggested_vendor_id ? (
                              <option value={`new:${row.suggested_vendor_name}`}>Create “{row.suggested_vendor_name}”</option>
                            ) : null}
                            {vendors.map((vendor) => (
                              <option key={vendor.id} value={`id:${vendor.id}`}>
                                {vendor.name}
                                {row.vendor_match?.id === vendor.id ? ` (${row.vendor_match.kind} match)` : ""}
                              </option>
                            ))}
                          </select>
                          <p className="mt-1 text-xs text-stone-500">
                            {row.vendor_exists
                              ? `Existing vendor: ${row.vendor_match?.name}`
                              : row.vendor_match
                                ? `Close match: ${row.vendor_match.name}`
                                : `Will create: ${row.suggested_vendor_name}`}
                          </p>
                        </>
                      ) : (
                        <span className="text-stone-600">{row.vendor_match?.name || row.suggested_vendor_name}</span>
                      )}
                    </td>
                    <td className="px-3 py-2 min-w-[12rem]">
                      {row.status === "new" ? (
                        <>
                          <select
                            className={inputClass}
                            value={row.categoryChoice}
                            onChange={(e) => patch(row.import_key, { categoryChoice: e.target.value })}
                          >
                            <option value="">None</option>
                            {categories.map((category) => (
                              <option key={category.id} value={category.id}>
                                {category.name}
                                {row.category_match?.id === category.id ? ` (${row.category_match.kind} match)` : ""}
                              </option>
                            ))}
                          </select>
                          <p className="mt-1 text-xs text-stone-500">
                            {row.category_match ? `${row.category_match.kind} match: ${row.category_match.name}` : "No category match"}
                          </p>
                        </>
                      ) : (
                        <span className="text-stone-600">{row.category_match?.name || "—"}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
