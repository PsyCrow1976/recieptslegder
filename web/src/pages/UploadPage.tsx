import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";

export default function UploadPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function onFile(next: File | null) {
    setFile(next);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(next ? URL.createObjectURL(next) : null);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token || !file) return;
    setLoading(true);
    setError("");
    try {
      const receipt = await api.scan(token, file);
      navigate(`/receipts/${receipt.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold">Scan a receipt</h2>
        <p className="text-stone-500">
          Photograph or upload a till slip. Tesseract runs on this server (no cloud). Harald Nyborg is recognised from
          column layout (varenr, qty, description, price). Review and correct before it is saved.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-4">
        <label className="block cursor-pointer rounded-xl border border-dashed border-stone-300 p-6 text-center hover:bg-stone-50">
          <input
            type="file"
            accept="image/jpeg,image/png,image/jpg"
            capture="environment"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          <span className="text-sm font-medium text-brand-700">Take a photo or choose an image</span>
          <p className="mt-1 text-xs text-stone-500">JPEG or PNG, up to 20 MB</p>
        </label>

        {preview && (
          <img src={preview} alt="Receipt preview" className="mx-auto max-h-96 rounded-lg border object-contain" />
        )}

        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={!file || loading}
          className="w-full rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Reading receipt…" : "Scan and review"}
        </button>
      </form>
    </div>
  );
}
