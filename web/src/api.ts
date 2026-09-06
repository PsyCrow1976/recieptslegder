const API_BASE = "/api/v1";

export type UserInfo = { id: string; username: string; is_admin: boolean };
export type PlatformKind = "bank" | "investment" | "other";

export type Person = {
  id: string;
  name: string;
  color: string;
  notes: string | null;
  created_at: string;
};

export type Platform = {
  id: string;
  name: string;
  kind: PlatformKind;
  website: string | null;
  color: string;
  notes: string | null;
  created_at: string;
  account_count: number;
};

export type Vendor = {
  id: string;
  name: string;
  website: string | null;
  notes: string | null;
  created_at: string;
};

export type Category = {
  id: string;
  name: string;
  color: string;
  notes: string | null;
  created_at: string;
};

export type AccountSummary = {
  id: string;
  name: string;
  account_number: string | null;
  currency: string;
  opening_balance_ore: number;
  balance_ore: number;
  notes: string | null;
  created_at: string;
  platform: Platform;
  owners: Person[];
  movement_count: number;
};

export type MovementItem = {
  id: string;
  position: number;
  description: string;
  vendor: Vendor | null;
  product_url: string | null;
  amount_ore: number;
  quantity: number;
};

export type Attachment = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
};

export type AccountBrief = {
  id: string;
  name: string;
  currency: string;
  platform_name: string;
  platform_kind: PlatformKind;
};

export type Movement = {
  id: string;
  account_id: string;
  posted_on: string;
  amount_ore: number;
  description: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  vendor: Vendor | null;
  categories: Category[];
  items: MovementItem[];
  attachments: Attachment[];
  items_sum_ore: number;
  items_sum_ok: boolean;
  account: AccountBrief;
};

export type MovementItemWrite = {
  description: string;
  vendor_id?: string | null;
  vendor_name?: string | null;
  product_url?: string | null;
  amount_ore: number;
  quantity: number;
};

export type ImportMatch = {
  id: string;
  name: string;
  score: number;
  kind: string;
};

export type ImportPreviewRow = {
  line_number: number;
  import_key: string;
  posted_on: string | null;
  amount_ore: number | null;
  name: string;
  description: string;
  label: string;
  currency: string;
  status: "new" | "duplicate" | "skipped";
  skip_reason: string | null;
  existing_movement_id: string | null;
  vendor_text: string;
  vendor_exists: boolean;
  vendor_match: ImportMatch | null;
  category_match: ImportMatch | null;
  suggested_vendor_name: string;
  suggested_vendor_id: string | null;
  suggested_category_id: string | null;
};

export type ImportPreview = {
  filename: string;
  detected_account_number: string | null;
  suggested_account_id: string | null;
  row_count: number;
  new_count: number;
  duplicate_count: number;
  skipped_count: number;
  rows: ImportPreviewRow[];
};

export type ImportCommitResult = {
  created: number;
  skipped_duplicate: number;
  skipped_missing: number;
};

export type MovementWrite = {
  account_id: string;
  posted_on: string;
  amount_ore?: number | null;
  description?: string;
  vendor_id?: string | null;
  vendor_name?: string | null;
  category_ids?: string[];
  notes?: string | null;
  items?: MovementItemWrite[];
};

export type Dashboard = {
  household_balance_ore: number;
  this_month_in_ore: number;
  this_month_out_ore: number;
  movement_count: number;
  account_count: number;
  people_count: number;
  platform_count: number;
  accounts: AccountSummary[];
  by_person: {
    person: Person;
    sole_balance_ore: number;
    shared_balance_ore: number;
    account_count: number;
  }[];
  by_category: { category: Category; movement_count: number; total_ore: number }[];
  recent: Movement[];
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

export function attachmentUrl(movementId: string, attachmentId: string): string {
  return `${API_BASE}/movements/${movementId}/attachments/${attachmentId}/file`;
}

export async function attachmentObjectUrl(
  token: string,
  movementId: string,
  attachmentId: string,
): Promise<string> {
  const response = await fetch(attachmentUrl(movementId, attachmentId), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Could not load file");
  return URL.createObjectURL(await response.blob());
}

export const api = {
  me: (token: string) => request<UserInfo>("/auth/me", token),
  dashboard: (token: string) => request<Dashboard>("/dashboard", token),

  people: (token: string) => request<Person[]>("/people", token),
  createPerson: (token: string, payload: { name: string; color: string; notes?: string }) =>
    request<Person>("/people", token, { method: "POST", body: JSON.stringify(payload) }),
  updatePerson: (token: string, id: string, payload: Partial<{ name: string; color: string; notes: string | null }>) =>
    request<Person>(`/people/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deletePerson: (token: string, id: string) => request<void>(`/people/${id}`, token, { method: "DELETE" }),

  platforms: (token: string) => request<Platform[]>("/platforms", token),
  createPlatform: (
    token: string,
    payload: { name: string; kind: PlatformKind; website?: string; color: string; notes?: string },
  ) => request<Platform>("/platforms", token, { method: "POST", body: JSON.stringify(payload) }),
  updatePlatform: (token: string, id: string, payload: Record<string, unknown>) =>
    request<Platform>(`/platforms/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deletePlatform: (token: string, id: string) => request<void>(`/platforms/${id}`, token, { method: "DELETE" }),

  accounts: (token: string) => request<AccountSummary[]>("/accounts", token),
  account: (token: string, id: string) => request<AccountSummary>(`/accounts/${id}`, token),
  createAccount: (
    token: string,
    payload: {
      platform_id: string;
      name: string;
      account_number?: string;
      currency: string;
      opening_balance_ore: number;
      owner_ids: string[];
      notes?: string;
    },
  ) => request<AccountSummary>("/accounts", token, { method: "POST", body: JSON.stringify(payload) }),
  updateAccount: (token: string, id: string, payload: Record<string, unknown>) =>
    request<AccountSummary>(`/accounts/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteAccount: (token: string, id: string) => request<void>(`/accounts/${id}`, token, { method: "DELETE" }),

  vendors: (token: string) => request<Vendor[]>("/vendors", token),
  createVendor: (token: string, payload: { name: string; website?: string; notes?: string }) =>
    request<Vendor>("/vendors", token, { method: "POST", body: JSON.stringify(payload) }),
  updateVendor: (token: string, id: string, payload: Record<string, unknown>) =>
    request<Vendor>(`/vendors/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteVendor: (token: string, id: string) => request<void>(`/vendors/${id}`, token, { method: "DELETE" }),

  categories: (token: string) => request<Category[]>("/categories", token),
  createCategory: (token: string, payload: { name: string; color: string; notes?: string }) =>
    request<Category>("/categories", token, { method: "POST", body: JSON.stringify(payload) }),
  updateCategory: (token: string, id: string, payload: Record<string, unknown>) =>
    request<Category>(`/categories/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteCategory: (token: string, id: string) => request<void>(`/categories/${id}`, token, { method: "DELETE" }),

  movements: (
    token: string,
    params?: { accountId?: string; personId?: string; categoryId?: string; q?: string },
  ) => {
    const search = new URLSearchParams();
    if (params?.accountId) search.set("account_id", params.accountId);
    if (params?.personId) search.set("person_id", params.personId);
    if (params?.categoryId) search.set("category_id", params.categoryId);
    if (params?.q) search.set("q", params.q);
    const query = search.toString();
    return request<Movement[]>(`/movements${query ? `?${query}` : ""}`, token);
  },
  movement: (token: string, id: string) => request<Movement>(`/movements/${id}`, token),
  createMovement: (token: string, payload: MovementWrite) =>
    request<Movement>("/movements", token, { method: "POST", body: JSON.stringify(payload) }),
  updateMovement: (token: string, id: string, payload: MovementWrite | Record<string, unknown>) =>
    request<Movement>(`/movements/${id}`, token, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteMovement: (token: string, id: string) => request<void>(`/movements/${id}`, token, { method: "DELETE" }),
  uploadAttachments: (token: string, id: string, files: File[]) => {
    const body = new FormData();
    files.forEach((file) => body.append("files", file));
    return request<Movement>(`/movements/${id}/attachments`, token, { method: "POST", body });
  },
  deleteAttachment: (token: string, movementId: string, attachmentId: string) =>
    request<Movement>(`/movements/${movementId}/attachments/${attachmentId}`, token, { method: "DELETE" }),
  previewImport: (token: string, file: File, accountId?: string) => {
    const body = new FormData();
    body.append("file", file);
    if (accountId) body.append("account_id", accountId);
    return request<ImportPreview>("/imports/preview", token, { method: "POST", body });
  },
  commitImport: (
    token: string,
    payload: {
      account_id: string;
      rows: {
        import_key: string;
        posted_on: string;
        amount_ore: number;
        description: string;
        vendor_id?: string | null;
        vendor_name?: string | null;
        category_ids?: string[];
      }[];
    },
  ) => request<ImportCommitResult>("/imports/commit", token, { method: "POST", body: JSON.stringify(payload) }),
};
