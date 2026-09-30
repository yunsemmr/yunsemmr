#!/usr/bin/env python3
"""README.md'yi GitHub profil görünümüne yakın bir yerel sayfaya çevirir.

Çıktı: onizleme/index.html (onizleme/ git'e girmez, yalnız yerel önizleme).
  - Markdown stili: onizleme/github-markdown-{light,dark}.css (github-markdown-css 5.8.1,
    MIT). Yoksa şu adreslerden bir kez indirilir:
    https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown-{light,dark}.css
  - SVG'ler onizleme/assets → ../assets bağlantısıyla gerçek dosyalardan gelir.
  - Katkı yılanı henüz yok (yayından sonraki ilk eylem koşusunda oluşur);
    README'deki yilan:basla/bitir arası yer tutucuyla değişir.

Sunmak için:
  python3 -m http.server <port> --bind 127.0.0.1 --directory onizleme
Gerekli paket: markdown-it-py.
"""

import pathlib
import re

from markdown_it import MarkdownIt

KOK = pathlib.Path(__file__).resolve().parent.parent
ONIZ = KOK / "onizleme"

YER_TUTUCU = """<div class="yilan-yer">
  <strong>Katkı yılanı yayından sonra oluşacak</strong>
  <span>.github/workflows/snake.yml ilk koşusunda <code>output</code> dalına yazılır.</span>
</div>"""

SAYFA = """<!doctype html>
<html lang="tr" data-tema="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>yunsemmr · profil önizleme</title>
<link id="md-acik" rel="stylesheet" href="github-markdown-light.css" media="(prefers-color-scheme: light)">
<link id="md-koyu" rel="stylesheet" href="github-markdown-dark.css" media="(prefers-color-scheme: dark)">
<style>
:root{--bg:#ffffff;--fg:#1f2328;--soluk:#59636e;--cizgi:#d1d9e0;--ust:#f6f8fa;--vurgu:#0f766e;
  --uyari-bg:#f1f8f6;--uyari-cizgi:#b7ddd5;--avatar-a:#14b8a6;--avatar-b:#0f766e;color-scheme:light}
@media (prefers-color-scheme: dark){html[data-tema="auto"]{--bg:#0d1117;--fg:#f0f6fc;--soluk:#9198a1;
  --cizgi:#3d444d;--ust:#010409;--vurgu:#5eead4;--uyari-bg:#0c1c22;--uyari-cizgi:#1d3a40;
  --avatar-a:#115e59;--avatar-b:#0b2a2c;color-scheme:dark}}
html[data-tema="koyu"]{--bg:#0d1117;--fg:#f0f6fc;--soluk:#9198a1;--cizgi:#3d444d;--ust:#010409;
  --vurgu:#5eead4;--uyari-bg:#0c1c22;--uyari-cizgi:#1d3a40;--avatar-a:#115e59;--avatar-b:#0b2a2c;
  color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif}
.ust{display:flex;align-items:center;gap:12px;padding:12px 24px;background:var(--ust);
  border-bottom:1px solid var(--cizgi)}
.ust .ad{font-weight:600}
.ust .etiket{color:var(--soluk);font-size:12px;border:1px solid var(--cizgi);border-radius:999px;padding:1px 8px}
.ust .bosluk{flex:1}
.tema{display:inline-flex;border:1px solid var(--cizgi);border-radius:6px;overflow:hidden}
.tema button{font:inherit;font-size:12px;color:var(--fg);background:transparent;border:0;padding:5px 10px;
  cursor:pointer;min-height:30px}
.tema button+button{border-left:1px solid var(--cizgi)}
.tema button[aria-pressed="true"]{background:var(--vurgu);color:var(--bg);font-weight:600}
.tema button:focus-visible{outline:2px solid var(--vurgu);outline-offset:-2px}
.kap{max-width:1280px;margin:0 auto;padding:24px 32px 48px;display:grid;grid-template-columns:296px 1fr;gap:24px}
.yan .avatar{width:100%;aspect-ratio:1;border-radius:50%;border:1px solid var(--cizgi);
  background:radial-gradient(circle at 30% 25%,var(--avatar-a),var(--avatar-b));
  display:grid;place-items:center;color:#fff;font-size:120px;font-weight:700;letter-spacing:-.02em}
.yan h1{margin:16px 0 0;font-size:24px;line-height:1.25;font-weight:600}
.yan .kullanici{margin:0;font-size:20px;font-weight:300;color:var(--soluk)}
.uyari{margin:0 0 16px;padding:10px 14px;border:1px solid var(--uyari-cizgi);background:var(--uyari-bg);
  border-radius:6px;font-size:13px;color:var(--soluk)}
.kutu{border:1px solid var(--cizgi);border-radius:6px;min-width:0}
.kutu .baslik{padding:10px 16px;border-bottom:1px solid var(--cizgi);font-size:12px;color:var(--soluk);
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.markdown-body{padding:24px 32px;background:transparent}
.markdown-body img{background:transparent}
.yilan-yer{display:flex;flex-direction:column;justify-content:center;align-items:center;gap:4px;
  aspect-ratio:880/192;max-width:880px;border:1px dashed var(--cizgi);border-radius:8px;
  color:var(--soluk);text-align:center;padding:12px;font-size:13px}
.yilan-yer strong{color:var(--fg);font-size:14px}
@media (max-width:767px){
  .ust{padding:10px 16px;flex-wrap:wrap}
  .kap{grid-template-columns:1fr;padding:16px 16px 40px;gap:16px}
  .yan{display:grid;grid-template-columns:64px 1fr;column-gap:12px;align-items:center}
  .yan .avatar{width:64px;font-size:28px;grid-row:span 2}
  .yan h1{margin:0;font-size:20px}
  .yan .kullanici{font-size:16px}
  .markdown-body{padding:16px}
}
</style>
</head>
<body>
<header class="ust">
  <span class="ad">yunsemmr</span><span class="etiket">yerel önizleme</span>
  <span class="bosluk"></span>
  <div class="tema" role="group" aria-label="Tema">
    <button type="button" data-tema="auto">Sistem</button>
    <button type="button" data-tema="acik">Açık</button>
    <button type="button" data-tema="koyu">Koyu</button>
  </div>
</header>
<main class="kap">
  <aside class="yan">
    <div class="avatar" aria-hidden="true">Y</div>
    <h1>Yunus</h1>
    <p class="kullanici">yunsemmr</p>
  </aside>
  <section>
    <p class="uyari">Yerel önizleme: bu sayfa GitHub'a gönderilmedi. Görseller depodaki SVG dosyalarından geliyor.</p>
    <div class="kutu">
      <div class="baslik">yunsemmr / README.md</div>
      <article class="markdown-body">
__README__
      </article>
    </div>
  </section>
</main>
<script>
(function () {
  var html = document.documentElement;
  var linkler = {acik: document.getElementById('md-acik'), koyu: document.getElementById('md-koyu')};
  var kaynaklar = Array.prototype.slice.call(document.querySelectorAll('picture source[media]'));
  kaynaklar.forEach(function (s) { s.dataset.asil = s.getAttribute('media'); });
  function uygula(tema) {
    html.dataset.tema = tema;
    if (tema === 'auto') {
      linkler.acik.media = '(prefers-color-scheme: light)';
      linkler.koyu.media = '(prefers-color-scheme: dark)';
    } else {
      linkler.acik.media = tema === 'acik' ? 'all' : 'not all';
      linkler.koyu.media = tema === 'koyu' ? 'all' : 'not all';
    }
    kaynaklar.forEach(function (s) {
      var asil = s.dataset.asil;
      if (tema === 'auto') { s.setAttribute('media', asil); return; }
      var koyuKaynak = asil.indexOf('dark') !== -1;
      s.setAttribute('media', (koyuKaynak === (tema === 'koyu')) ? 'all' : 'not all');
    });
    document.querySelectorAll('.tema button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.tema === tema));
    });
    try { history.replaceState(null, '', tema === 'auto' ? location.pathname : '?tema=' + tema); } catch (e) {}
  }
  document.querySelectorAll('.tema button').forEach(function (b) {
    b.addEventListener('click', function () { uygula(b.dataset.tema); });
  });
  var istenen = new URLSearchParams(location.search).get('tema');
  uygula(istenen === 'acik' || istenen === 'koyu' ? istenen : 'auto');
})();
</script>
</body>
</html>
"""


def main():
    md = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")
    kaynak = (KOK / "README.md").read_text(encoding="utf-8")
    govde = md.render(kaynak)
    govde, n = re.subn(r"<!-- yilan:basla -->.*?<!-- yilan:bitir -->", YER_TUTUCU, govde, flags=re.S)
    if n != 1:
        raise SystemExit("README'de yilan:basla/bitir işaretleri bulunamadı")
    ONIZ.mkdir(exist_ok=True)
    for tema in ("light", "dark"):
        if not (ONIZ / f"github-markdown-{tema}.css").exists():
            raise SystemExit(f"onizleme/github-markdown-{tema}.css yok; belge başındaki adresten indir.")
    baglanti = ONIZ / "assets"
    if not baglanti.exists():
        baglanti.symlink_to("../assets")
    (ONIZ / "index.html").write_text(SAYFA.replace("__README__", govde), encoding="utf-8")
    print("yazıldı: onizleme/index.html")


if __name__ == "__main__":
    main()
