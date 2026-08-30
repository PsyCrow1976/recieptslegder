const API_BASE = "/api/v1";

export type UserInfo = {
  id: string;
  username: string;
  is_admin: boolean;
};

export type Tag = {
  id: string;
  name: string;
  color: string;
  notes: string | null;
  created_at: string;
};

export type Product = {
  id: string;
  item_number: string;
  title: string | null;
  url: string | null;
  image_url: string | null;
  last_web_price_ore: number | null;
  status: string;
  last_fetched_at: string | null;
};

export type ReceiptLine = {
  id: string;
  position: number;
  item_number: string | null;
  quantity: number;
  description: string;
  line_total_ore: number;
  unit_price_ore: number;
  product: Product | null;
};

export type Receipt = {
  id: string;
  vendor_id: string | null;
  vendor_name: string;
  store_name: string | null;
  store_address: string | null;
  cvr: string | null;
  purchased_at: string | null;
  register_no: string | null;
  invoice_no: string | null;
  payment_method: string | null;
  total_ore: number;
  vat_ore: number;
  barcode: string | null;
  cashier: string | null;
  status: string;
  needs_training: boolean;
  lines_sum_ok: boolean;
  vat_ok: boolean;
  notes: string | null;
  created_at: string;
  lines: ReceiptLine[];
  tags: Tag[];
  warnings: string[];
  image_url: string | null;
};

export type TagSpend = {
  tag: Tag;
  receipt_count: number;
  total_ore: number;
};

export type Dashboard = {
  this_month_ore: number;
  all_time_ore: number;
  receipt_count: number;
  training_count: number;
  by_tag: TagSpend[];
  by_vendor: { vendor_name: string; receipt_count: number; total_ore: number }[];
};

export type CalendarDay = {
  date: string;
  receipt_count: number;
  total_ore: number;
  receipts: Receipt[];
};

export type LineWrite = {
  item_number: string | null;
  quantity: number;
  description: string;
  line_total_ore: number;
};

async function request<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    const message =
      typeof detail.detail === "string"
        ? detail.detail
        : Array.isArray(detail.detail)
          ? detail.detail.map((item: { msg?: string }) => item.msg).join(", ")
          : "Request failed";
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<string> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error("Invalid username or password");
  }
  const data = await response.json();
  return data.access_token as string;
}

export async function receiptImageObjectUrl(token: string, receiptId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/receipts/${receiptId}/image`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error("Could not load receipt image");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export const api = {
  me: (token: string) => request<UserInfo>("/auth/me", token),
  tags: (token: string) => request<Tag[]>("/tags", token),
  createTag: (token: string, payload: { name: string; color: string; notes?: string }) =>
    request<Tag>("/tags", token, { method: "POST", body: JSON.stringify(payload) }),
  updateTag: (token: string, id: string, payload: { name?: string; color?: string; notes?: string | null }) =>
    request<Tag>(`/tags/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteTag: (token: string, id: string) => request<void>(`/tags/${id}`, token, { method: "DELETE" }),
  tagSpend: (token: string, id: string) => request<TagSpend>(`/tags/${id}/spend`, token),
  dashboard: (token: string) => request<Dashboard>("/dashboard", token),
  calendar: (token: string, year: number, month: number) =>
    request<CalendarDay[]>(`/calendar?year=${year}&month=${month}`, token),
  receipts: (
    token: string,
    params?: { tagId?: string; q?: string; day?: string; includeDrafts?: boolean; needsTraining?: boolean },
  ) => {
    const search = new URLSearchParams();
    if (params?.tagId) search.set("tag_id", params.tagId);
    if (params?.q) search.set("q", params.q);
    if (params?.day) search.set("day", params.day);
    if (params?.includeDrafts) search.set("include_drafts", "true");
    if (params?.needsTraining) search.set("needs_training", "true");
    const query = search.toString();
    return request<Receipt[]>(`/receipts${query ? `?${query}` : ""}`, token);
  },
  receipt: (token: string, id: string) => request<Receipt>(`/receipts/${id}`, token),
  scan: (token: string, file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<Receipt>("/receipts/scan", token, { method: "POST", body });
  },
  updateReceipt: (
    token: string,
    id: string,
    payload: {
      vendor_name?: string;
      store_name?: string | null;
      purchased_at?: string | null;
      invoice_no?: string | null;
      payment_method?: string | null;
      total_ore?: number;
      vat_ore?: number;
      notes?: string | null;
      status?: string;
      needs_training?: boolean;
      tag_ids?: string[];
      lines?: LineWrite[];
    },
  ) => request<Receipt>(`/receipts/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteReceipt: (token: string, id: string) => request<void>(`/receipts/${id}`, token, { method: "DELETE" }),
  lookupProducts: (token: string, id: string) =>
    request<Receipt>(`/receipts/${id}/lookup-products`, token, { method: "POST" }),
};
