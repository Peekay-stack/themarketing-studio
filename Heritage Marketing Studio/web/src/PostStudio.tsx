import React from "react";
import { api, type Deliverable, type ChatMessage, type User, type Platform, type CreativeModel } from "./api";
import { Pill, ApprovalBar, platformMeta } from "./components";

export function PostStudio({
  postId, user, platforms, creativeModels, onBack, toast,
}: {
  postId: string; user: User; platforms: Platform[]; creativeModels: CreativeModel[];
  onBack: () => void; toast: (m: string) => void;
}) {
  const [d, setD] = React.useState<Deliverable | null>(null);
  const [msgs, setMsgs] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const logRef = React.useRef<HTMLDivElement>(null);

  const load = React.useCallback(async () => {
    setD(await api.deliverable(postId));
    setMsgs(await api.chat(postId));
  }, [postId]);
  React.useEffect(() => { load(); }, [load]);
  React.useEffect(() => { logRef.current?.scrollTo(0, logRef.current.scrollHeight); }, [msgs]);

  if (!d) return <p className="muted">Loading…</p>;

  const m = platformMeta(platforms, d.platform);
  const editable = d.status === "Draft" || d.status === "Changes";
  const isCreator = user.id === d.creator_id;
  const authority = { Creator: 0, ApproverL1: 1, ApproverL2: 2, ApproverL3: 3 }[user.role] ?? 0;
  const canApprove = d.status === "Pending" && !isCreator && d.current_level != null && authority >= d.current_level;
  const isVideo = d.content_type === "Video";
  const models = creativeModels.filter((x) => (isVideo ? x.kind === "video" : x.kind === "image"));

  const send = async () => {
    if (!input.trim()) return;
    const text = input; setInput(""); setBusy(true);
    setMsgs((m) => [...m, { id: "tmp", role: "user", content: text, created_at: "" }]);
    try {
      const updated = await api.sendChat(d.id, text);
      setD(updated);
      setMsgs(await api.chat(d.id));
    } catch (e: any) { toast(e.message); }
    setBusy(false);
  };

  const regenCreative = async (model_id: string) => {
    setBusy(true);
    try { setD(await api.setCreative(d.id, model_id)); toast("Creative updated"); } catch (e: any) { toast(e.message); }
    setBusy(false);
  };

  const act = async (fn: () => Promise<Deliverable>, msg: string) => {
    setBusy(true);
    try { setD(await fn()); toast(msg); } catch (e: any) { toast(e.message); }
    setBusy(false);
  };

  return (
    <div>
      <button className="back" onClick={onBack}>← Back to brief</button>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div className="page-title" style={{ fontSize: 22 }}>
          <span style={{ color: m.accent }}>{m.name}</span> {d.content_type}
        </div>
        <Pill status={d.status} />
      </div>

      <ApprovalBar status={d.status} requiredLevels={d.required_levels} currentLevel={d.current_level} approvals={d.approvals} />

      <div className="btn-row" style={{ marginBottom: 16 }}>
        {editable && isCreator && <button className="btn primary" onClick={() => act(() => api.submitDeliverable(d.id), "Submitted")} disabled={busy}>Submit for approval</button>}
        {canApprove && <button className="btn primary" onClick={() => act(() => api.approveDeliverable(d.id), `Approved L${d.current_level}`)} disabled={busy}>Approve (L{d.current_level})</button>}
        {canApprove && <button className="btn" onClick={() => act(() => api.changesDeliverable(d.id, "Please revise"), "Changes requested")} disabled={busy}>Request changes</button>}
        {d.status === "Approved" && <button className="btn gold" onClick={() => act(() => api.publishDeliverable(d.id), "Published (stub)")} disabled={busy}>Publish → Live</button>}
        {d.status === "Pending" && !canApprove && <span className="muted" style={{ alignSelf: "center" }}>Waiting on Level {d.current_level} approver.</span>}
      </div>

      {d.brand_flags.length > 0 && <div className="flags">⚠ {d.brand_flags.join(" · ")}</div>}

      <div className="studio">
        {/* Live preview */}
        <div className="preview">
          <div className="ptop">
            <div className="avatar" style={{ background: m.accent }}>{m.name[0]}</div>
            <div>
              <div className="pname">{m.handle}</div>
              <div className="psub">{m.sub}</div>
            </div>
          </div>
          <div className="media">
            {d.creative_url ? <img src={d.creative_url} alt="creative" /> : <span className="muted">No creative yet — generate one →</span>}
          </div>
          <div className="pcap">{d.caption}</div>
          {d.hashtags.length > 0 && <div className="ptags">{d.hashtags.join(" ")}</div>}
        </div>

        {/* Chat + creative */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="chat">
            <div className="clog" ref={logRef}>
              {msgs.length === 0 && <div className="muted" style={{ fontSize: 13 }}>Refine this post by chatting — e.g. “make it warmer”, “add a festive Diwali angle”, “shorten for Instagram”, “stronger CTA”.</div>}
              {msgs.map((mm, i) => <div key={i} className={`msg ${mm.role}`}>{mm.content}</div>)}
              {busy && <div className="msg assistant">…</div>}
            </div>
            <div className="cinput">
              <input
                placeholder={editable ? "Tell the studio how to refine this post…" : "Locked — only editable while Draft/Changes"}
                value={input} disabled={!editable || busy}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
              />
              <button className="btn primary" disabled={!editable || busy} onClick={send}>Send</button>
            </div>
          </div>

          {editable && (
            <div className="card">
              <strong>Creative — {isVideo ? "Video Studio" : "Social Studio"}</strong>
              <div className="muted" style={{ fontSize: 12.5, margin: "4px 0 8px" }}>
                Pick a model to (re)generate the {isVideo ? "video" : "image"}. Current: {d.creative_model || "none"}.
              </div>
              <div className="chips">
                {models.map((x) => (
                  <div key={x.id} className={`chip ${d.creative_model === x.id ? "sel" : ""}`} title={x.note}
                       style={{ cursor: "pointer" }} onClick={() => regenCreative(x.id)}>
                    {x.label}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
