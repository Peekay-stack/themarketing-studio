// bridge.js — makes the Heritage front end's AI work against this backend.
// The app calls window.claude.complete({messages}) and expects the completion text back.
// Here we define it to POST to /complete on the same origin. No app logic is changed.
(function () {
  const BASE = ""; // same origin (served by FastAPI)
  if (!window.claude) window.claude = {};
  window.claude.complete = async function (opts) {
    try {
      const res = await fetch(BASE + "/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: (opts && opts.messages) || [] }),
      });
      if (!res.ok) return "";
      const data = await res.json();
      return data.completion || "";
    } catch (e) {
      // On any failure, return "" so the app uses its own graceful fallback.
      return "";
    }
  };
  console.log("[Heritage] window.claude.complete bridged to backend /complete");
})();
