import React from "react";
import { api, API_BASE, type FormatSchema, type Brief } from "./api";

// map builder field keys -> Brief columns
const MAP: Record<string, string> = {
  background: "background_context", businessObjective: "business_objective", commObjective: "communication_objective",
  audience: "target_consumer", insight: "consumer_insight", competition: "competitive_context",
  proposition: "single_minded_proposition", rtbs: "reasons_to_believe", tone: "tone_personality",
  mandatories: "mandatories_brand_codes", deliverables: "deliverables_channels", budget: "budget",
  timeline: "timeline_milestones", kpis: "success_metrics_kpis",
};

const SRC_LABEL: Record<string, string> = { builder: "builder format", frontend: "front-end format", skill: "skill" };

export function Builder({ onSaved, objectives }: { onSaved: (id: string) => void; objectives: string[] }) {
  const [schema, setSchema] = React.useState<FormatSchema[]>([]);
  const [fmtId, setFmtId] = React.useState("comms");
  const [tab, setTab] = React.useState(0);
  const [values, setValues] = React.useState<Record<string, string>>({});
  const [title, setTitle] = React.useState("");
  const [objective, setObjective] = React.useState(objectives[0] || "Brand awareness");
  const [ask, setAsk] = React.useState("");
  const [reviewing, setReviewing] = React.useState(false);
  const [status, setStatus] = React.useState("");
  const [drafting, setDrafting] = React.useState(false);

  React.useEffect(() => { api.briefSchema().then(setSchema); }, []);
  React.useEffect(() => { setTab(0); setValues({}); setTitle(""); setReviewing(false); setStatus(""); }, [fmtId]);

  const fmt = schema.find((s) => s.id === fmtId);
  const allFields = () => fmt ? fmt.sections.flatMap((s) => s.fields) : [];

  const set = (k: string, v: string) => setValues((p) => ({ ...p, [k]: v }));

  const draftAll = async () => {
    if (!ask.trim() || !fmt) return;
    setDrafting(true); setStatus("Drafting…");
    const keys = allFields().map((f) => `"${f[0]}" (${f[1]})`).join(", ");
    const prompt =
      `You are drafting a ${fmt.name} brief for Heritage (Indian dairy, brand line 'Pure Doodh Ki Shakti'). ` +
      `The ask: ${ask}. Return ONLY a JSON object with exactly these keys: ${keys}. Each value 1-2 sentences, concrete and on-brand.`;
    try {
      const r = await api.complete([{ role: "user", content: prompt }]);
      if (!r.completion) { setStatus("AI drafting needs ANTHROPIC_API_KEY on the server. Fill fields manually."); setDrafting(false); return; }
      let txt = r.completion; txt = txt.slice(txt.indexOf("{"), txt.lastIndexOf("}") + 1);
      const obj = JSON.parse(txt);
      const next: Record<string, string> = { ...values };
      allFields().forEach((f) => { if (obj[f[0]] != null) next[f[0]] = String(obj[f[0]]); });
      setValues(next);
      if (!title) setTitle(`${fmt.name} brief — Pure Milk`);
      setStatus("Draft ready — review each tab, tweak, then Review.");
    } catch (e: any) { setStatus("Could not draft (" + e.message + "). Fill fields manually."); }
    setDrafting(false);
  };

  const mapToBrief = (): Partial<Brief> => {
    const b: any = { title: title || (fmt?.name || "Brief") + " brief", brief_type: fmt?.name || "Comms", campaign_objective: objective };
    const overflow: string[] = [];
    allFields().forEach((f) => {
      const v = values[f[0]] || "";
      if (MAP[f[0]]) b[MAP[f[0]]] = v;
      else if (v) overflow.push(f[1] + ": " + v);
    });
    if (overflow.length) b.background_context = ((b.background_context || "") + "\n\n" + overflow.join("\n")).trim();
    return b;
  };

  const save = async (thenSubmit: boolean) => {
    setStatus("Saving…");
    try {
      const brief = await api.createBrief(mapToBrief());
      if (thenSubmit) { await api.submitBrief(brief.id); setStatus("✓ Saved and submitted — now in the approval queue (needs L1–L3)."); }
      else setStatus("✓ Saved to Briefs.");
      onSaved(brief.id);
    } catch (e: any) { setStatus("Could not save (" + e.message + ")."); }
  };

  if (!fmt) return <p className="muted">Loading builder…</p>;

  return (
    <div>
      <div className="page-title">New brief</div>
      <div className="page-sub">Pick a format, build it tab by tab (or let the AI co-writer draft it), then review the ready-to-approve brief.</div>

      <div className="chips" style={{ marginBottom: 16 }}>
        {schema.map((s) => (
          <button key={s.id} className={"chip" + (s.id === fmtId ? " sel" : "")} onClick={() => setFmtId(s.id)}
            style={{ cursor: "pointer", border: s.id === fmtId ? "1px solid var(--gold)" : "1px solid var(--line)", fontWeight: 700 }}>
            {s.name}{s.source !== "frontend" && <span className="pill" style={{ marginLeft: 6, fontSize: 10 }}>{SRC_LABEL[s.source]}</span>}
          </button>
        ))}
      </div>

      {fmt.uses_skill ? (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", background: "#FFF7E8", fontSize: 13, color: "#7a5a10" }}>
            Brand strategy briefs use the full builder — NeedScope wheel, CB/CA → DB/DA, market-share Excel and consumer research — and generate a paginated Word brief.
          </div>
          <iframe title="brand-builder" src={API_BASE + "/brand-brief-builder"} style={{ width: "100%", height: 1400, border: "none" }} />
        </div>
      ) : reviewing ? (
        <ReadyToApprove fmt={fmt} values={values} title={title || fmt.name + " brief"} objective={objective}
          onBack={() => setReviewing(false)} onSubmit={() => save(true)} status={status} />
      ) : (
        <>
          <div className="row2" style={{ marginBottom: 14 }}>
            <div><label>Brief title</label><input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={`${fmt.name} brief — Pure Milk`} /></div>
            <div><label>Campaign objective</label>
              <select value={objective} onChange={(e) => setObjective(e.target.value)}>{objectives.map((o) => <option key={o}>{o}</option>)}</select>
            </div>
          </div>

          <div className="cowriter">
            <div style={{ fontWeight: 700, marginBottom: 6 }}>✦ AI co-writer <span className="muted" style={{ fontWeight: 400 }}>— describe the ask, I'll draft every field</span></div>
            <div style={{ display: "flex", gap: 10 }}>
              <input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="e.g. Diwali push for Pure Milk targeting young urban families" style={{ flex: 1 }} />
              <button className="btn gold" disabled={drafting} onClick={draftAll}>{drafting ? "Drafting…" : "Draft brief"}</button>
            </div>
          </div>

          <div className="steps" style={{ borderBottom: "1px solid var(--line)", paddingBottom: 0, marginBottom: 16 }}>
            {fmt.sections.map((s, i) => (
              <button key={i} onClick={() => setTab(i)} className="btn" style={{
                border: "none", borderBottom: i === tab ? "2px solid var(--green2)" : "2px solid transparent",
                borderRadius: 0, background: "none", color: i === tab ? "var(--green)" : "var(--muted)", fontWeight: 700,
              }}>{s.title}</button>
            ))}
          </div>

          {fmt.sections[tab].fields.map((f, idx) => (
            <div className="card" key={f[0]} style={{ marginBottom: 12 }}>
              <label style={{ marginTop: 0 }}><span className="tag" style={{ width: 22, height: 22, display: "inline-grid", fontSize: 11, marginRight: 8, verticalAlign: "middle", background: "#EAF2EC", color: "var(--green2)" }}>{idx + 1}</span>{f[1]}</label>
              <textarea value={values[f[0]] || ""} placeholder={f[2]} onChange={(e) => set(f[0], e.target.value)} style={{ minHeight: 70 }} />
            </div>
          ))}

          <div className="btn-row" style={{ marginTop: 8 }}>
            <button className="btn" onClick={() => setReviewing(true)}>Review brief →</button>
            <button className="btn primary" onClick={() => save(false)}>Save to Briefs</button>
          </div>
          {status && <p className="muted" style={{ marginTop: 10 }}>{status}</p>}
        </>
      )}
    </div>
  );
}

function ReadyToApprove({ fmt, values, title, objective, onBack, onSubmit, status }:
  { fmt: FormatSchema; values: Record<string, string>; title: string; objective: string; onBack: () => void; onSubmit: () => void; status: string }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div><div className="page-title">{title}</div>
          <div className="chips"><span className="chip">{fmt.name}</span><span className="chip">{objective}</span></div></div>
        <span className="pill Draft">Draft</span>
      </div>
      {fmt.sections.map((s) => (
        <div key={s.title}>
          <div className="muted" style={{ fontSize: 12, fontWeight: 800, letterSpacing: ".06em", textTransform: "uppercase", margin: "18px 0 8px" }}>{s.title}</div>
          {s.fields.map((f) => (
            <div className="card" key={f[0]} style={{ marginBottom: 10, background: "#FCFAF4" }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{f[1]}</div>
              <div style={{ whiteSpace: "pre-wrap", color: values[f[0]] ? "var(--ink)" : "var(--muted)" }}>{values[f[0]] || "—"}</div>
            </div>
          ))}
        </div>
      ))}
      <div className="btn-row" style={{ marginTop: 10 }}>
        <button className="btn" onClick={onBack}>← Back to builder</button>
        <button className="btn primary" onClick={onSubmit}>Save & submit for approval</button>
      </div>
      {status && <p className="muted" style={{ marginTop: 10 }}>{status}</p>}
    </div>
  );
}
