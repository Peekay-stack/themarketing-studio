import React from "react";
import type { Approval, Platform } from "./api";

export function Pill({ status }: { status: string }) {
  return <span className={`pill ${status}`}>{status}</span>;
}

const TAGS: Record<string, { t: string; bg: string; fg: string }> = {
  IMC: { t: "IM", bg: "#FCEFC7", fg: "#A77A00" },
  Media: { t: "ME", bg: "#E6F0FB", fg: "#0A66C2" },
  Packaging: { t: "PK", bg: "#FBE3E1", fg: "#C0392B" },
  Comms: { t: "CO", bg: "#EAF6EC", fg: "#1E7E34" },
};
export function BriefTag({ type }: { type: string }) {
  const c = TAGS[type] || TAGS.Comms;
  return <div className="tag" style={{ background: c.bg, color: c.fg }}>{c.t}</div>;
}

export function platformMeta(platforms: Platform[], id: string): Platform {
  return (
    platforms.find((p) => p.id === id || p.name.toLowerCase() === id.toLowerCase()) || {
      id, name: id, accent: "#14331F", handle: "Heritage Foods", sub: "", studio: "social",
    }
  );
}

/** The flexible multi-level approval chain, visualised. */
export function ApprovalBar({
  status, requiredLevels, currentLevel, approvals,
}: { status: string; requiredLevels: number[]; currentLevel: number | null; approvals: Approval[] }) {
  const signed = new Set(approvals.map((a) => a.level));
  return (
    <div className="approvalbar">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <strong>Approval chain</strong>
        <Pill status={status} />
      </div>
      <div className="steps">
        <div className="step">
          <div className="dot" style={{ background: "#E7E0D0" }}>✎</div>
          <span>Creator</span>
        </div>
        <span className="arrow">→</span>
        {requiredLevels.map((lvl, i) => {
          const done = signed.has(lvl) || status === "Approved" || status === "Live";
          const current = status === "Pending" && currentLevel === lvl;
          return (
            <React.Fragment key={lvl}>
              <div className={`step ${done ? "done" : ""} ${current ? "current" : ""}`}>
                <div className="dot">{done ? "✓" : `L${lvl}`}</div>
                <span>Level {lvl}</span>
              </div>
              {i < requiredLevels.length - 1 && <span className="arrow">→</span>}
            </React.Fragment>
          );
        })}
        <span className="arrow">→</span>
        <div className={`step ${status === "Approved" || status === "Live" ? "done" : ""}`}>
          <div className="dot">★</div>
          <span>Approved</span>
        </div>
      </div>
      <div className="muted" style={{ fontSize: 12.5 }}>
        Chain length is set by policy ({requiredLevels.length} level{requiredLevels.length > 1 ? "s" : ""}).
        Creators can’t approve their own work; a higher level may cover a lower one.
      </div>
    </div>
  );
}

export function useToast() {
  const [msg, setMsg] = React.useState<string | null>(null);
  const show = (m: string) => { setMsg(m); window.setTimeout(() => setMsg(null), 2600); };
  const node = msg ? <div className="toast">{msg}</div> : null;
  return { show, node };
}
