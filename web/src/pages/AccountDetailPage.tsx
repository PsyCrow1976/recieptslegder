import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type AccountSummary, type Movement } from "../api";
import { useAuth } from "../auth";
import { Chip, EmptyState, Money, PageHeader, btnGhost, btnPrimary, cardClass } from "../components/ui";
import { formatDate } from "../money";

export default function AccountDetailPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([api.account(token!, id), api.movements(token!, { accountId: id })])
      .then(([a, m]) => {
        setAccount(a);
        setMovements(m);
      })
      .catch((err: Error) => setError(err.message));
  }, [id, token]);

  async function remove() {
    if (!id || !confirm("Delete this account and all of its entries?")) return;
    await api.deleteAccount(token!, id);
    navigate("/accounts");
  }

  if (error) return <p className="text-rose-700">{error}</p>;
  if (!account) return <p className="text-stone-500">Loading…</p>;

  return (
    <div>
      <PageHeader
        title={account.name}
        subtitle={`${account.platform.name} · ${account.currency}${account.account_number ? ` · ${account.account_number}` : ""}`}
        action={
          <div className="flex gap-2">
            <Link to={`/entries/new?account=${account.id}`} className={btnPrimary}>
              Add entry
            </Link>
            <button type="button" className={btnGhost} onClick={remove}>
              Delete
            </button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Balance</p>
          <div className="mt-2 text-2xl">
            <Money ore={account.balance_ore} className="text-2xl" />
          </div>
        </div>
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Opening</p>
          <div className="mt-2">
            <Money ore={account.opening_balance_ore} />
          </div>
        </div>
        <div className={cardClass}>
          <p className="text-xs uppercase tracking-wide text-stone-500">Owners</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {account.owners.map((owner) => (
              <Chip key={owner.id} label={owner.name} color={owner.color} />
            ))}
          </div>
        </div>
      </div>

      <h2 className="mt-8 text-lg text-ink">Entries</h2>
      {movements.length === 0 ? (
        <div className="mt-3">
          <EmptyState
            title="No money in or out yet"
            body="Add a salary, a purchase, a transfer, or an investment movement. You can attach a PDF or a photo of a receipt and split it into line items."
            to={`/entries/new?account=${account.id}`}
            cta="Add entry"
          />
        </div>
      ) : (
        <div className="mt-3 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {movements.map((m) => (
            <Link
              key={m.id}
              to={`/entries/${m.id}`}
              className="flex items-center justify-between gap-4 border-b border-stone-100 px-4 py-3 last:border-b-0 hover:bg-stone-50"
            >
              <div>
                <p className="font-medium">{m.description || m.vendor?.name || "Entry"}</p>
                <p className="text-xs text-stone-500">
                  {formatDate(m.posted_on)}
                  {m.vendor ? ` · ${m.vendor.name}` : ""}
                  {m.items.length ? ` · ${m.items.length} items` : ""}
                  {m.attachments.length ? ` · ${m.attachments.length} files` : ""}
                </p>
              </div>
              <Money ore={m.amount_ore} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
