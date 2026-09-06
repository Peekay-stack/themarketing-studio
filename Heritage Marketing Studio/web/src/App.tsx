import React from "react";
import { api, setUser, type User, type Platform, type CreativeModel } from "./api";
import { useToast } from "./components";
import { BriefList } from "./BriefList";
import { BriefDetail } from "./BriefDetail";
import { PostStudio } from "./PostStudio";
import { ApprovalQueue } from "./ApprovalQueue";
import { Builder } from "./Builder";

type View =
  | { name: "briefs" }
  | { name: "brief"; id: string }
  | { name: "post"; id: string; briefId?: string }
  | { name: "queue" }
  | { name: "builder" };

export function App() {
  const [users, setUsers] = React.useState<User[]>([]);
  const [user, setUserState] = React.useState<User | null>(null);
  const [platforms, setPlatforms] = React.useState<Platform[]>([]);
  const [models, setModels] = React.useState<CreativeModel[]>([]);
  const [objectives, setObjectives] = React.useState<string[]>([]);
  const [view, setView] = React.useState<View>({ name: "briefs" });
  const [lastBrief, setLastBrief] = React.useState<string | null>(null);
  const toast = useToast();

  React.useEffect(() => {
    api.users().then((us) => { setUsers(us); const c = us.find((u) => u.role === "Creator") || us[0]; if (c) { setUser(c.id); setUserState(c); } });
    api.catalog().then((c) => { setPlatforms(c.platforms); setObjectives(c.campaign_objectives); });
    api.creativeModels().then(setModels);
  }, []);

  const switchUser = (id: string) => { setUser(id); setUserState(users.find((u) => u.id === id) || null); };

  const openBuilder = () => setView({ name: "builder" });

  if (!user) return <div className="container"><p className="muted">Connecting to API…</p></div>;

  return (
    <div className="app">
      <div className="header">
        <div className="logo">Heritage <span className="dot">●</span> Marketing Studio</div>
        <nav>
          <button className={view.name === "builder" ? "active" : ""} onClick={() => setView({ name: "builder" })}>New brief</button>
          <button className={view.name === "briefs" || view.name === "brief" ? "active" : ""} onClick={() => setView({ name: "briefs" })}>Briefs</button>
          <button className={view.name === "queue" ? "active" : ""} onClick={() => setView({ name: "queue" })}>Approval queue</button>
          <a className="studio-link" href="/studio">Full studio ↗</a>
        </nav>
        <div className="spacer" />
        <div className="userswitch">
          <span className="role-chip">{user.role.replace("Approver", "L")}</span>
          <select value={user.id} onChange={(e) => switchUser(e.target.value)}>
            {users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
        </div>
      </div>

      <div className="container">
        {view.name === "briefs" && <BriefList onOpen={(id) => { setLastBrief(id); setView({ name: "brief", id }); }} onNew={openBuilder} />}
        {view.name === "brief" && (
          <BriefDetail
            briefId={view.id} user={user} platforms={platforms} creativeModels={models}
            onOpenPost={(id) => setView({ name: "post", id, briefId: view.id })}
            onBack={() => setView({ name: "briefs" })} toast={toast.show}
          />
        )}
        {view.name === "post" && (
          <PostStudio
            postId={view.id} user={user} platforms={platforms} creativeModels={models}
            onBack={() => setView(view.briefId ? { name: "brief", id: view.briefId } : lastBrief ? { name: "brief", id: lastBrief } : { name: "briefs" })}
            toast={toast.show}
          />
        )}
        {view.name === "builder" && (
          <Builder objectives={objectives} onSaved={(id) => { setLastBrief(id); setView({ name: "brief", id }); }} />
        )}
        {view.name === "queue" && (
          <ApprovalQueue
            user={user} platforms={platforms}
            onOpenBrief={(id) => { setLastBrief(id); setView({ name: "brief", id }); }}
            onOpenPost={(id) => setView({ name: "post", id })}
          />
        )}
      </div>
      {toast.node}
    </div>
  );
}
