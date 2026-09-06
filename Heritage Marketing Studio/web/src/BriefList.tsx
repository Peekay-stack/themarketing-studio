import React from "react";
import { api, type Brief } from "./api";
import { Pill, BriefTag } from "./components";

export function BriefList({ onOpen, onNew }: { onOpen: (id: string) => void; onNew: () => void }) {
  const [briefs, setBriefs] = React.useState<Brief[] | null>(null);
  React.useEffect(() => { api.briefs().then(setBriefs); }, []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="page-title">Briefs</div>
          <div className="page-sub">Campaign briefs route through approval before any content is generated.</div>
        </div>
        <button className="btn gold" onClick={onNew}>+ New brief</button>
      </div>
      {!briefs ? (
        <p className="muted">Loading…</p>
      ) : (
        <div className="grid cols-3">
          {briefs.map((b) => (
            <div key={b.id} className="card click" onClick={() => onOpen(b.id)}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <BriefTag type={b.brief_type} />
                <Pill status={b.status} />
              </div>
              <h3>{b.title}</h3>
              <div className="meta">{b.brief_type} · {b.campaign_objective}</div>
              <div className="meta" style={{ marginTop: 8 }}>
                {b.required_levels.length}-level approval
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
