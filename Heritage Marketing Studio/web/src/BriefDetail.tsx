import React from "react";
import { api, getUserId, type Brief, type Deliverable, type User, type Platform, type CreativeModel } from "./api";
import { Pill, ApprovalBar, platformMeta } from "./components";

const FIELDS: [keyof Brief, string, boolean][] = [
  ["single_minded_proposition", "Single-minded proposition", true],
  ["communication_objective", "Communication objective", true],
  ["target_consumer", "Target consumer", true],
  ["consumer_insight", "Consumer insight", true],
  ["tone_personality", "Tone & personality", true],
  ["mandatories_brand_codes", "Mandatories & brand codes", true],
  ["reasons_to_believe", "Reasons to believe", true],
  ["background_context", "Background & context", true],
  ["competitive_context", "Competitive context", true],
  ["deliverables_channels", "Deliverables & channels", false],
  ["timeline_milestones", "Timeline & milestones", false],
  ["success_metrics_kpis", "Success metrics / KPIs", false],
];

export function BriefDetail({
  briefId, user, platforms, creativeModels, onOpenPost, onBack, toast,
}: {
  briefId: string; user: User; platforms: Platform[]; creativeModels: CreativeModel[];
  onOpenPost: (id: string) => void; onBack: () => void; toast: (m: string) => void;
}) {
  const [b, setB] = React.useState<Brief | null>(null);
  const [posts, setPosts] = React.useState<Deliverable[]>([]);
  const [busy, setBusy] = React.useState(false);
  const [showMore, setShowMore] = React.useState(false);

  const refresh = React.useCallback(async () => {
    setB(await api.brief(briefId));
    setPosts(await api.deliverables(briefId));
  }, [briefId]);
  React.useEffect(() => { refresh(); }, [refresh]);

  if (!b) return <p className="muted">Loading…</p>;

  const editable = b.status === "Draft" || b.status === "Changes";
  const isCreator = user.id === b.creator_id;
  const authority = { Creator: 0, ApproverL1: 1, ApproverL2: 2, ApproverL3: 3 }[user.role] ?? 0;
  const canApprove = b.status === "Pending" && !isCreator && b.current_level != null && authority >= b.current_level;

  const set = (k: keyof Brief, v: string) => setB({ ...b, [k]: v } as Brief);
  const save = async () => { setBusy(true); try { setB(await api.updateBrief(b.id, b)); toast("Brief saved"); } catch (e: any) { toast(e.message); } setBusy(false); };
  const act = async (fn: () => Promise<Brief>, msg: string) => { setBusy(true); try { await fn(); await refresh(); toast(msg); } catch (e: any) { toast(e.message); } setBusy(false); };

  return (
    <div>
      <button className="back" onClick={onBack}>← All briefs</button>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div style={{ flex: 1 }}>
          {editable && isCreator ? (
            <input value={b.title} onChange={(e) => set("title", e.target.value)} style={{ fontSize: 20, fontWeight: 700 }} />
          ) : (
            <div className="page-title">{b.title}</div>
          )}
          <div className="page-sub">{b.brief_type} · {b.campaign_objective}</div>
        </div>
        <Pill status={b.status} />
      </div>

      <ApprovalBar status={b.status} requiredLevels={b.required_levels} currentLevel={b.current_level} approvals={b.approvals} />

      {/* Approval actions */}
      <div className="btn-row" style={{ marginBottom: 18 }}>
        {editable && isCreator && <button className="btn" onClick={save} disabled={busy}>Save</button>}
        {editable && isCreator && <button className="btn primary" onClick={() => act(() => api.submitBrief(b.id), "Submitted for approval")} disabled={busy}>Submit for approval</button>}
        {canApprove && <button className="btn primary" onClick={() => act(() => api.approveBrief(b.id), `Approved level ${b.current_level}`)} disabled={busy}>Approve (L{b.current_level})</button>}
        {canApprove && <button className="btn" onClick={() => act(() => api.changesBrief(b.id, "Please revise"), "Changes requested")} disabled={busy}>Request changes</button>}
        {b.status === "Pending" && !canApprove && <span className="muted" style={{ alignSelf: "center" }}>Waiting on Level {b.current_level} approver.</span>}
      </div>

      {/* Brief fields */}
      <div className="card">
        {editable && isCreator ? (
          <>
            <div className="row2">
              <div>
                <label>Brief type</label>
                <select className="field" value={b.brief_type} onChange={(e) => set("brief_type", e.target.value)}>
                  {["Comms", "IMC", "Media", "Packaging"].map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label>Campaign objective</label>
                <select className="field" value={b.campaign_objective} onChange={(e) => set("campaign_objective", e.target.value)}>
                  {["Brand awareness", "Product launch", "Festive / seasonal", "Performance / DR", "Trust & purity", "Recipe / usage"].map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
            </div>
            {FIELDS.filter((f) => showMore || f[2]).map(([k, lbl]) => (
              <div key={k}>
                <label>{lbl}</label>
                <textarea value={(b[k] as string) || ""} onChange={(e) => set(k, e.target.value)} />
              </div>
            ))}
            <button className="back" style={{ marginTop: 12 }} onClick={() => setShowMore(!showMore)}>{showMore ? "Show fewer fields" : "Show all fields"}</button>
          </>
        ) : (
          <div className="grid cols-2">
            {FIELDS.filter((f) => f[2]).map(([k, lbl]) => (
              <div key={k}>
                <label>{lbl}</label>
                <div style={{ fontSize: 14 }}>{(b[k] as string) || <span className="muted">—</span>}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Studio / generation — gated on Approved */}
      <div style={{ marginTop: 24 }}>
        <div className="page-title" style={{ fontSize: 20 }}>Studio</div>
        {b.status !== "Approved" ? (
          <div className="card" style={{ background: "var(--cream)" }}>
            <strong>Generation is locked.</strong>
            <div className="muted" style={{ marginTop: 4 }}>
              A brief must be <b>Approved</b> before the Social/Video Studio can generate content.
              Current status: <Pill status={b.status} />
            </div>
          </div>
        ) : (
          <GeneratePanel brief={b} platforms={platforms} creativeModels={creativeModels} onGenerated={refresh} toast={toast} />
        )}
      </div>

      {/* Posts */}
      {posts.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div className="page-title" style={{ fontSize: 20 }}>Posts ({posts.length})</div>
          <div className="grid cols-3">
            {posts.map((p) => {
              const m = platformMeta(platforms, p.platform);
              return (
                <div key={p.id} className="card click" onClick={() => onOpenPost(p.id)}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontWeight: 700, color: m.accent }}>{m.name}</span>
                    <Pill status={p.status} />
                  </div>
                  <div className="meta" style={{ margin: "6px 0" }}>{p.content_type} · {p.format}</div>
                  <div style={{ fontSize: 13, lineHeight: 1.45, maxHeight: 60, overflow: "hidden" }}>{p.caption}</div>
                  {p.brand_flags.length > 0 && <div className="meta" style={{ color: "#C0392B", marginTop: 6 }}>⚠ {p.brand_flags.length} brand flag(s)</div>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function GeneratePanel({
  brief, platforms, creativeModels, onGenerated, toast,
}: { brief: Brief; platforms: Platform[]; creativeModels: CreativeModel[]; onGenerated: () => void; toast: (m: string) => void; }) {
  const social = platforms.filter((p) => p.studio === "social");
  const [picked, setPicked] = React.useState<string[]>(social.map((p) => p.id));
  const [contentType, setContentType] = React.useState("Post");
  const [model, setModel] = React.useState<string>(creativeModels.find((m) => m.kind === "image")?.id || "");
  const [busy, setBusy] = React.useState(false);

  const toggle = (id: string) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));
  const isVideo = contentType === "Video";
  const models = creativeModels.filter((m) => (isVideo ? m.kind === "video" : m.kind === "image"));

  React.useEffect(() => { setModel(models[0]?.id || ""); }, [contentType]); // eslint-disable-line

  const go = async () => {
    setBusy(true);
    try {
      const targets = picked.map((pid) => ({ platform: pid, format: isVideo ? "Video" : "Static", content_type: contentType }));
      await api.generate(brief.id, targets, model || undefined);
      toast(`Generated ${targets.length} ${isVideo ? "video" : "post"}(s)`);
      onGenerated();
    } catch (e: any) { toast(e.message); }
    setBusy(false);
  };

  return (
    <div className="card">
      <strong>{isVideo ? "Video Studio" : "Social Studio"}</strong>
      <div className="muted" style={{ fontSize: 13, marginBottom: 6 }}>
        One idea → {social.map((s) => s.name).join(", ")} with live previews. Refine each post in chat afterwards.
      </div>
      <label>Platforms</label>
      <div className="chips">
        {platforms.map((p) => (
          <div key={p.id} className={`chip ${picked.includes(p.id) ? "sel" : ""}`} onClick={() => toggle(p.id)} style={{ cursor: "pointer" }}>
            <span style={{ color: p.accent, fontWeight: 700 }}>●</span> {p.name}
          </div>
        ))}
      </div>
      <div className="row2" style={{ marginTop: 10 }}>
        <div>
          <label>Content type</label>
          <select className="field" value={contentType} onChange={(e) => setContentType(e.target.value)}>
            {["Post", "Video", "Campaign"].map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label>Creative model ({isVideo ? "video" : "image"})</label>
          <select className="field" value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="">No creative (copy only)</option>
            {models.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </div>
      </div>
      <div className="btn-row" style={{ marginTop: 14 }}>
        <button className="btn gold" disabled={busy || picked.length === 0} onClick={go}>
          {busy ? "Generating…" : `Generate ${picked.length} ${isVideo ? "video" : "post"}(s)`}
        </button>
      </div>
    </div>
  );
}
