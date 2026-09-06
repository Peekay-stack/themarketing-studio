// api.ts — typed client for the Heritage Marketing Studio API.
// Empty BASE = same origin (when the built app is served by FastAPI). For `vite dev`,
// set VITE_API_URL=http://localhost:8000.
const BASE = (import.meta as any).env?.VITE_API_URL || "";

let currentUserId = "puneet";
export function setUser(id: string) { currentUserId = id; }
export function getUserId() { return currentUserId; }

async function req<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const res = await fetch(BASE + path, {
    method,
    headers: { "Content-Type": "application/json", "X-User-Id": currentUserId },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export type User = { id: string; name: string; role: string };
export type Platform = { id: string; name: string; accent: string; handle: string; sub: string; studio: string };
export type CreativeModel = { id: string; label: string; kind: string; note: string };
export type Approval = { level: number; approver_id: string; role: string };

export type Brief = {
  id: string; title: string; brief_type: string; campaign_objective: string;
  background_context: string; business_objective: string; communication_objective: string;
  target_consumer: string; consumer_insight: string; competitive_context: string;
  single_minded_proposition: string; reasons_to_believe: string; tone_personality: string;
  mandatories_brand_codes: string; deliverables_channels: string; timeline_milestones: string;
  success_metrics_kpis: string; budget: string; budget_value: number;
  creator_id: string; status: string; required_levels: number[]; current_level: number | null;
  approvals: Approval[]; history: any[]; created_at: string;
};

export type Deliverable = {
  id: string; brief_id: string; platform: string; format: string; content_type: string;
  caption: string; hashtags: string[]; rationale: string; brand_flags: string[];
  creative_kind: string | null; creative_model: string | null; creative_url: string | null;
  creator_id: string; status: string; required_levels: number[]; current_level: number | null;
  approvals: Approval[]; history: any[]; created_at: string;
};

export type ChatMessage = { id: string; role: string; content: string; created_at: string };

export type BriefField = [string, string, string]; // key, label, hint
export type BriefSection = { title: string; fields: BriefField[] };
export type FormatSchema = { id: string; name: string; uses_skill: boolean; source: string; sections: BriefSection[] };

export const API_BASE = BASE;

export const api = {
  me: () => req<User>("/me"),
  users: () => req<User[]>("/users"),
  catalog: () => req<{ brief_types: string[]; content_types: string[]; campaign_objectives: string[]; platforms: Platform[] }>("/catalog"),
  creativeModels: (kind?: string) => req<CreativeModel[]>(`/creative-models${kind ? `?kind=${kind}` : ""}`),

  briefs: () => req<Brief[]>("/briefs"),
  brief: (id: string) => req<Brief>(`/briefs/${id}`),
  createBrief: (b: Partial<Brief>) => req<Brief>("/briefs", "POST", b),
  updateBrief: (id: string, b: Partial<Brief>) => req<Brief>(`/briefs/${id}`, "PUT", b),
  submitBrief: (id: string) => req<Brief>(`/briefs/${id}/submit`, "POST"),
  approveBrief: (id: string) => req<Brief>(`/briefs/${id}/approve`, "POST"),
  changesBrief: (id: string, note: string) => req<Brief>(`/briefs/${id}/request-changes`, "POST", { note }),
  generate: (id: string, targets: { platform: string; format: string; content_type: string }[], creative_model?: string) =>
    req<Deliverable[]>(`/briefs/${id}/generate`, "POST", { targets, creative_model }),

  deliverables: (brief_id?: string, status?: string) => {
    const q = new URLSearchParams();
    if (brief_id) q.set("brief_id", brief_id);
    if (status) q.set("status", status);
    return req<Deliverable[]>(`/deliverables?${q}`);
  },
  deliverable: (id: string) => req<Deliverable>(`/deliverables/${id}`),
  editDeliverable: (id: string, body: { caption?: string; hashtags?: string[] }) => req<Deliverable>(`/deliverables/${id}`, "PUT", body),
  submitDeliverable: (id: string) => req<Deliverable>(`/deliverables/${id}/submit`, "POST"),
  approveDeliverable: (id: string) => req<Deliverable>(`/deliverables/${id}/approve`, "POST"),
  changesDeliverable: (id: string, note: string) => req<Deliverable>(`/deliverables/${id}/request-changes`, "POST", { note }),
  publishDeliverable: (id: string) => req<Deliverable>(`/deliverables/${id}/publish`, "POST"),
  setCreative: (id: string, model_id: string, prompt?: string) => req<Deliverable>(`/deliverables/${id}/creative`, "POST", { model_id, prompt }),

  chat: (id: string) => req<ChatMessage[]>(`/deliverables/${id}/chat`),
  sendChat: (id: string, message: string) => req<Deliverable>(`/deliverables/${id}/chat`, "POST", { message }),

  briefSchema: () => req<FormatSchema[]>("/brief-schema"),
  complete: (messages: { role: string; content: string }[]) =>
    req<{ completion: string; live: boolean }>("/complete", "POST", { messages }),
};
