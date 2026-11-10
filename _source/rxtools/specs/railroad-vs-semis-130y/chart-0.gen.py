#!/usr/bin/env python3
# Generated chart (no Korean original to inpaint): python3 chart-0.gen.py <lang> full|card <out.png>. Data: rail-1871-1903.csv (Shiller/Cowles monthly).
"""Railroad (Cowles-Shiller) 1871-1903 chart in the same style as the SOX chart (chart-1).
   python3 rail_chart.py <lang> <mode> <out.png>      mode: full (1600x1013) | card (inset for the card)"""
import sys, csv, datetime as dt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib import font_manager as fm

lang, mode, out = sys.argv[1], sys.argv[2], sys.argv[3]
FAM = {'ko': 'Noto Sans CJK KR', 'ja': 'Noto Sans CJK JP', 'en': 'Noto Sans CJK KR', 'es': 'Noto Sans CJK KR'}[lang]
plt.rcParams['font.family'] = FAM

BG, FG, GRID, AX = '#0e1726', '#ffffff', '#33405a', '#3a4863'
GOLD, RED, MUTED, SUB = '#efb23e', '#fd5b5f', '#8e9bb2', '#c3cad6'

T = {
 'ko': dict(title='원조 철도주: 19세기 강세장 속 30~50% 조정을 세 번 겪었다',
            sub='코울스-실러 주가지수(1900년 이전 사실상 철도지수), 월평균·로그 스케일, 1871.1 ~ 1903.12',
            leg='코울스-실러 지수 (월평균)',
            pre='1차 상승(1861~72) +200%는\nBofA·GFD 기준, 코울스는 1871년 시작',
            src='자료: Shiller/Cowles(Yale), BofA Global Investment Strategy·GFD. 월평균이라 일간 고점·저점보다 등락폭이 작게 나옴'),
 'en': dict(title='The original railroad stocks: three 30–50% corrections in a 19th-century bull market',
            sub='Cowles-Shiller stock index (effectively a railroad index before 1900), monthly avg. · log scale, Jan 1871 ~ Dec 1903',
            leg='Cowles-Shiller index (monthly avg.)',
            pre='Rally 1 (1861~72) +200% is BofA/GFD;\nthe Cowles series starts in 1871',
            src='Source: Shiller/Cowles (Yale), BofA Global Investment Strategy · GFD. Monthly averages swing less than daily highs and lows'),
 'es': dict(title='Las ferroviarias originales: tres correcciones del 30–50% en el alza del siglo XIX',
            sub='Índice Cowles-Shiller (de hecho un índice ferroviario antes de 1900), promedio mensual · escala log., ene 1871 ~ dic 1903',
            leg='Índice Cowles-Shiller (promedio mensual)',
            pre='El alza 1 (1861~72) +200% es de BofA/GFD;\nla serie Cowles empieza en 1871',
            src='Fuente: Shiller/Cowles (Yale), BofA Global Investment Strategy · GFD. El promedio mensual oscila menos que los extremos diarios'),
 'ja': dict(title='元祖・鉄道株：19世紀の強気相場で30~50%の調整を3度経験した',
            sub='コウルズ-シラー株価指数（1900年以前は事実上の鉄道指数）、月平均・対数目盛、1871.1 ~ 1903.12',
            leg='コウルズ-シラー指数（月平均）',
            pre='第1次上昇（1861~72）+200%はBofA・GFD基準、\nコウルズは1871年開始',
            src='出所：Shiller/Cowles（Yale）、BofA Global Investment Strategy・GFD。月平均のため日次の高値・安値より騰落幅は小さい'),
}[lang]

d, v = [], []
for r in csv.DictReader(open(sys.argv[4] if len(sys.argv) > 4 else
                              __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'rail-1871-1903.csv'))):
    t = dt.date.fromisoformat(r['Date'])
    if t.year <= 1903:
        d.append(t); v.append(float(r['SP500']))
D = lambda y, m: dt.date(y, m, 1)
val = dict(zip(d, v))

card = mode == 'card'
W, H = (1600, 1013) if not card else (1000, 620)
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100 if not card else 100)
fig.patch.set_facecolor(BG)
s = 1.0 if not card else 0.62          # font scale
L, R, B, Tp = (0.08, 0.96, 0.12, 0.82) if not card else (0.085, 0.965, 0.12, 0.80)
ax = fig.add_axes([L, B, R - L, Tp - B]); ax.set_facecolor(BG)
ax.plot(d, v, color=FG, lw=3.0 * (1 if not card else .75), solid_joinstyle='round', zorder=3, label=T['leg'])
ax.set_yscale('log')
ticks = [2.5, 3, 4, 5, 6, 8, 10]
ax.set_yticks(ticks); ax.set_yticklabels([('%g' % t) for t in ticks]); ax.minorticks_off()
ax.set_ylim(2.3, 11.2)
ax.set_xlim(D(1870, 10), D(1904, 6))
ax.xaxis.set_major_locator(md.YearLocator(5, month=1, day=1)); ax.xaxis.set_major_formatter(md.DateFormatter('%Y'))
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
for sp in ('left', 'bottom'): ax.spines[sp].set_color(AX)
ax.tick_params(colors=SUB, labelsize=15 * s, length=5 * s, color=AX)

def arrow(p0, p1, col, txt, tx, ty, off, ha='center', fs=24):
    (a, b), (c, e) = p0, p1
    ax.annotate('', xy=(D(*c), val[D(*c)] * off[1]), xytext=(D(*a), val[D(*a)] * off[0]),
                arrowprops=dict(arrowstyle='-|>,head_length=0.7,head_width=0.35', color=col, lw=3.2 * (1 if not card else .75),
                                shrinkA=0, shrinkB=0), zorder=4)
    ax.text(D(*tx), ty, txt, color=col, fontsize=fs * s, fontweight='bold', ha=ha, va='center', zorder=5)

# peaks / troughs (monthly): 1872.4, 1877.6, 1881.6, 1896.8, 1902.9, 1903.10
arrow(((1872, 4), (1872, 4)), ((1877, 6), (1877, 6)), RED, '-47%', (1876, 1), 5.6, (1.07, 1.07))
arrow(((1877, 6), (1877, 6)), ((1881, 6), (1881, 6)), GOLD, '+141%', (1880, 6), 3.25, (0.94, 0.94))
arrow(((1881, 6), (1881, 6)), ((1896, 8), (1896, 8)), RED, '-42%', (1889, 1), 7.4, (1.1, 1.1))
arrow(((1896, 8), (1896, 8)), ((1902, 9), (1902, 9)), GOLD, '+132%', (1900, 9), 4.3, (0.88, 0.92))
arrow(((1902, 9), (1902, 9)), ((1903, 10), (1903, 10)), RED, '-29%', (1903, 6), 10.0, (1.08, 1.08))
if not card: ax.text(D(1882, 6), 2.62, T['pre'], color=MUTED, fontsize=13.5 * s, ha='left', va='center', linespacing=1.45, zorder=5)

lg = ax.legend(loc='upper left', frameon=False, fontsize=16 * s, handlelength=2.6, borderaxespad=0.8)
for t in lg.get_texts(): t.set_color(FG)

# title block
fig.patches.append(matplotlib.patches.Rectangle((0.019 if not card else 0.012, 0.86 if not card else 0.845), 0.0065 if not card else 0.006,
                                                0.11 if not card else 0.125, transform=fig.transFigure, color=RED, zorder=5))
tx0 = 0.035 if not card else 0.03
fig.canvas.draw()
rend = fig.canvas.get_renderer()
def fit(x, y, txt, fs, maxx, **kw):
    t = fig.text(x, y, txt, fontsize=fs, va='center', **kw)
    while t.get_window_extent(rend).x1 > maxx * fig.bbox.width and fs > 6:
        fs *= 0.97; t.set_fontsize(fs)
    return t
fit(tx0, 0.935 if not card else 0.925, T['title'], (31 if lang in ('ko', 'ja') else 27) * s, 0.975, color=FG, fontweight='bold')
fit(tx0, 0.882 if not card else 0.862, T['sub'], (20 if lang in ('ko', 'ja') else 17) * s, 0.975, color=SUB)
cr = fig.text(0.965, 0.038 if not card else 0.035, 'stayhungryasi.com', color=MUTED, fontsize=17 * s, ha='right', va='center')
fit(tx0, 0.038 if not card else 0.035, T['src'], (15 if lang in ('ko', 'ja') else 13) * s,
    (cr.get_window_extent(rend).x0 - 25) / fig.bbox.width, color=SUB, fontweight='bold')
fig.savefig(out, facecolor=BG, dpi=100 if not card else 200)
print('wrote', out)
