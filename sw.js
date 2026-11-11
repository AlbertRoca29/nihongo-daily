const SHELL = "nihongo-shell-v16";
const FONTS = "nihongo-fonts-v2";
const OFFLINE = "nihongo-offline-v1";   // the last 7 lessons and their audio, refreshed by the app on wifi
const FILES = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("nihongo-shell-") && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// The app sends the list of files to keep offline; anything else in that cache is dropped.
self.addEventListener("message", e => {
  const d = e.data || {};
  if (d.type !== "precache" || !Array.isArray(d.urls)) return;
  e.waitUntil((async () => {
    const c = await caches.open(OFFLINE), want = new Set(d.urls.map(u => new URL(u, self.registration.scope).href));
    for (const req of await c.keys()) if (!want.has(req.url)) await c.delete(req);
    for (const u of want){
      const hit = await c.match(u);
      if (hit && /\.(mp3|svg|png|woff2)$/.test(u)) continue;   // audio and images never change: keep
      try{ const r = await fetch(u, {cache: "no-cache"}); if (r.ok) await c.put(u, r); }catch{}
    }
  })());
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com"){
    e.respondWith(caches.open(FONTS).then(c => c.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (r.ok || r.type === "opaque") c.put(e.request, r.clone());
      return r;
    }))));
    return;
  }
  if (url.origin !== location.origin) return;
  // audio, stickers, icons and fonts are named by content: cache first
  if (/\/(audio|icons|fonts)\/.+\.(mp3|svg|png|woff2)$/.test(url.pathname)){
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (r.ok){ const copy = r.clone(); caches.open(SHELL).then(c => c.put(e.request, copy)); }
      return r;
    })));
    return;
  }
  // everything else: network first, cache as fallback (new lessons always show, old ones work offline)
  e.respondWith(fetch(e.request).then(r => {
    const copy = r.clone(); caches.open(SHELL).then(c => c.put(e.request, copy)); return r;
  }).catch(() => caches.match(e.request, {ignoreSearch: true})));
});
