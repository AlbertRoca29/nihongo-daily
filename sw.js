const SHELL = "nihongo-shell-v10";
const FONTS = "nihongo-fonts-v1";
const FILES = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", e => { e.waitUntil(self.clients.claim()); });
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  // Google Fonts: cache first, so the app keeps its fonts offline instead of falling back to the phone's
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com"){
    e.respondWith(caches.open(FONTS).then(c => c.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (r.ok || r.type === "opaque") c.put(e.request, r.clone());
      return r;
    }))));
    return;
  }
  if (url.origin !== location.origin) return;
  // Network first, fall back to cache (so new lessons always show, old ones work offline)
  e.respondWith(fetch(e.request).then(r => {
    const copy = r.clone(); caches.open(SHELL).then(c => c.put(e.request, copy)); return r;
  }).catch(() => caches.match(e.request)));
});
