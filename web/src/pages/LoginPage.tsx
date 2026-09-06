import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api";
import { useAuth } from "../auth";
import { btnPrimary, inputClass } from "../components/ui";

export default function LoginPage() {
  const { setToken } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const token = await login(username, password);
      setToken(token);
      navigate("/");
    } catch {
      setError("Login failed. Check username and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-widest text-brand-700">Family finances</p>
        <h1 className="mt-2 text-3xl text-ink">Household Ledger</h1>
        <p className="mt-1 text-sm text-stone-500">Sign in to manage people, accounts, and money in and out.</p>

        <label className="mt-6 block text-sm font-medium text-stone-700">
          Username
          <input
            className={`${inputClass} mt-1`}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </label>
        <label className="mt-4 block text-sm font-medium text-stone-700">
          Password
          <input
            type="password"
            className={`${inputClass} mt-1`}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error && <p className="mt-4 text-sm text-rose-700">{error}</p>}
        <button type="submit" disabled={loading} className={`${btnPrimary} mt-6 w-full`}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
