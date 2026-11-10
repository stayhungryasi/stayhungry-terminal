// Rebuild card-02 (railroad) in the same layout as card-03 (SOX): chart inset + three cycle boxes.
// node card02.mjs   -> writes card02.<lang>.png next to this script (chart images: card_<lang>.png)
import { chromium } from '/home/claude/.npm-global/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const D = process.argv[2] || './';  // folder holding card_<lang>.png from chart-0.gen.py card; writes card02.<lang>.png
const T = {
  ko: { tag: '원본 교차검증', right: 'BofA · 코울스-실러', h1: '철도주는 강세장 속', h2: '30~50% 조정', h2b: '을 세 번', h2first: false,
        box: ['1차 1861~77', '2차 1877~96', '3차 1896~1903'], cw: '코울스',
        note: '큰 숫자는 BofA(GFD), 작은 숫자는 코울스-실러 월평균. 코울스는 1871년 시작이라 1차 상승은 데이터 없음.',
        src: '자료: BofA Global Investment Strategy·GFD, Shiller/Cowles', fam: "'Noto Sans CJK KR'" },
  en: { tag: 'Cross-checking the original', right: 'BofA · Cowles-Shiller', h1: 'Railroads, inside a bull market,', h2: 'corrected 30~50%', h2b: ' three times', h2first: true,
        box: ['Cycle 1 · 1861~77', 'Cycle 2 · 1877~96', 'Cycle 3 · 1896~1903'], cw: 'Cowles',
        note: 'Large figures: BofA (GFD). Small: Cowles-Shiller monthly averages, which start in 1871, so rally 1 has no Cowles data.',
        src: 'Source: BofA Global Investment Strategy·GFD, Shiller/Cowles', fam: "'Noto Sans CJK KR'" },
  es: { tag: 'Verificación del original', right: 'BofA · Cowles-Shiller', h1: 'Los ferrocarriles, en plena alza,', h2: 'corrigieron 30~50%', h2b: ' tres veces', h2first: true,
        box: ['Ciclo 1 · 1861~77', 'Ciclo 2 · 1877~96', 'Ciclo 3 · 1896~1903'], cw: 'Cowles',
        note: 'Cifras grandes: BofA (GFD). Pequeñas: promedios mensuales de Cowles-Shiller, que empiezan en 1871; el alza 1 no tiene datos de Cowles.',
        src: 'Fuente: BofA Global Investment Strategy·GFD, Shiller/Cowles', fam: "'Noto Sans CJK KR'" },
  ja: { tag: '原典の検証', right: 'BofA · コウルズ-シラー', h1: '鉄道株は強気相場の中で', h2: '30~50%の調整', h2b: 'を3回', h2first: false,
        box: ['第1次 1861~77', '第2次 1877~96', '第3次 1896~1903'], cw: 'コウルズ',
        note: '大きい数字はBofA（GFD）、小さい数字はコウルズ-シラー月平均。コウルズは1871年開始のため第1次上昇はデータなし。',
        src: '出所：BofA Global Investment Strategy·GFD, Shiller/Cowles', fam: "'Noto Sans CJK JP'" },
};
const V = [['+200%', '-50%', '-47%'], ['+150%', '-45%', '+141% / -42%'], ['+170%', '-30%', '+132% / -29%']];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
for (const [lg, t] of Object.entries(T)) {
  const img = 'data:image/png;base64,' + fs.readFileSync(D + `card_${lg}.png`).toString('base64');
  const boxes = t.box.map((n, i) => `<div class="bx"><div class="bl">${n}</div><div class="up">${V[i][0]}</div><div class="dn">${V[i][1]}</div><div class="cw">${t.cw} ${V[i][2]}</div></div>`).join('');
  const big = (lg === 'en' || lg === 'es') ? 58 : 64;
  await p.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{width:1080px;height:1350px;background:#0e1726;font-family:${t.fam},sans-serif;color:#fff;position:relative;overflow:hidden}
  .hd{position:absolute;left:80px;right:80px;top:88px;display:flex;justify-content:space-between;align-items:center}
  .tag{font-size:25px;font-weight:700;color:#e8edf5}.tag b{color:#efb23e;margin-right:10px}
  .rt{font-size:24px;color:#8e9bb2}
  h1{position:absolute;left:78px;top:150px;font-size:${big}px;line-height:1.3;font-weight:900;letter-spacing:-1px}
  h1 em{font-style:normal;color:#fd595e}
  .ch{position:absolute;left:96px;top:352px;width:888px}
  .ch img{width:888px;display:block}
  .bxs{position:absolute;left:80px;top:932px;display:flex;gap:16px}
  .bx{width:296px;height:212px;background:#15213b;border-radius:20px;padding:24px 26px}
  .bl{font-size:${lg === 'ja' || lg === 'ko' ? 25 : 22}px;color:#a7b2c5}
  .up{font-size:48px;font-weight:900;margin-top:10px;line-height:1.08}
  .dn{font-size:48px;font-weight:900;color:#fd595e;line-height:1.08}
  .cw{font-size:19px;color:#8e9bb2;margin-top:6px}
  .nt{position:absolute;left:80px;right:80px;top:1158px;font-size:${lg === 'ko' || lg === 'ja' ? 18 : 17}px;line-height:1.45;color:#8e9bb2}
  .ln{position:absolute;left:80px;right:80px;top:1233px;height:2px;background:#29314a}
  .ft{position:absolute;left:80px;right:80px;top:1258px;display:flex;justify-content:space-between;font-size:23px;color:#a7b2c5}
  .ft b{color:#fff;font-weight:700}
  </style></head><body>
  <div class="hd"><div class="tag"><b>01</b>${t.tag}</div><div class="rt">${t.right}</div></div>
  <h1>${t.h1}<br>${t.h2first ? `<em>${t.h2}</em>${t.h2b}` : `<em>${t.h2}</em>${t.h2b}`}</h1>
  <div class="ch"><img src="${img}"></div>
  <div class="bxs">${boxes}</div>
  <div class="nt">${t.note}</div>
  <div class="ln"></div>
  <div class="ft"><span>${t.src}</span><b>02 / 09</b></div>
  </body></html>`);
  await p.evaluate(() => document.fonts.ready);
  const ov = await p.evaluate(() => { const h = document.querySelector('h1').getBoundingClientRect(), c = document.querySelector('.ch').getBoundingClientRect(), n = document.querySelector('.nt').getBoundingClientRect(); return { h1b: h.bottom, chb: c.bottom, chT: c.top, ntb: n.bottom, h1w: h.width }; });
  console.log(lg, JSON.stringify(ov));
  await p.screenshot({ path: D + `card02.${lg}.png` });
}
await b.close();
