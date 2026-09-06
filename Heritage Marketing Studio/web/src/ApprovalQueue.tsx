import React from "react";
import { api, type Brief, type Deliverable, type User, type Platform } from "./api";
import { Pill, platformMeta } from "./components";

export function ApprovalQueue({
  user, platforms, onOpenBrief, onOpenPost,
}: { user: User; platforms: Platform[]; onOpenBrief: (id: string) => void; onOpenPost: (id: string) => void; }) {
  const [briefs, setBriefs] = React.useState<Brief[]>([]);
  const [posts, setPosts] = React.useState<Deliverable[]>([]);
  React.useEffect(() => {
    api.briefs().then((bs) => setBriefs(bs.filter((b) => b.status === "Pending")));
    api.deliverables(undefined, "Pending").then(setPosts);
  }, []);

  const authority = { Creator: 0, ApproverL1: 1, ApproverL2: 2, ApproverL3: 3 }[user.role] ?? 0;
  const mine = (lvl: number | null, creator: string) => lvl != null && authority >= lvl && creator !== user.id;

  return (
    <div>
      <div className="page-title">Approval queue</div>
      <div className="page-sub">Items waiting for review. As {user.name}, you can act on the ones at or below your level.</div>

      <div className="page-title" style={{ fontSize: 18 }}>Briefs</div>
      {briefs.length === 0 ? <p className="muted">No briefs pending.</p> : (
        <div className="grid cols-2">
          {briefs.map((b) => (
            <div key={b.id} className="card click" onClick={() => onOpenBrief(b.id)}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{b.title}</strong><Pill status={b.status} />
              </div>
              <div className="meta" style={{ marginTop: 6 }}>
                Awaiting Level {b.current_level} {mine(b.current_level, b.creator_id) ? "· you can approve" : "· not your level"}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="page-title" style={{ fontSize: 18, marginTop: 22 }}>Posts</div>
      {posts.length === 0 ? <p className="muted">No posts pending.</p> : (
        <div className="grid cols-3">
          {posts.map((p) => {
            const m = platformMeta(platforms, p.platform);
            return (
              <div key={p.id} className="card click" onClick={() => onOpenPost(p.id)}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontWeight: 700, color: m.accent }}>{m.name}</span><Pill status={p.status} />
                </div>
                <div style={{ fontSize: 13, marginTop: 6, maxHeight: 54, overflow: "hidden" }}>{p.caption}</div>
                <div className="meta" style={{ marginTop: 6 }}>
                  Level {p.current_level} {mine(p.current_level, p.creator_id) ? "· you can approve" : "· not your level"}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
