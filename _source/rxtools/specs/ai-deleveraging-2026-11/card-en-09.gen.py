import json
from PIL import ImageFont
FD='/usr/share/fonts/opentype/noto/NotoSansCJK-'
def L(w,s,lang): return ImageFont.truetype(FD+w+'.ttc',int(round(s)),index=0 if lang=='ja' else 1)
HAIR=' '
WHITE="#f3f8fe"; GRAY="#cbd4e3"; RED="#ff5d63"
def filler(bold,size,lang):
    wb=L('Bold',size,lang).getlength(bold)
    return HAIR*int(round(wb/L('Regular',size,lang).getlength(HAIR)))
def pair(target,texts,size=30,boldcolor=WHITE,right=990,x0=None):
    """texts: {lang:(bold, rest)} -> two regions on the same box/rect, bold drawn last"""
    key={'boxes':target} if isinstance(target,list) and isinstance(target[0],int) and len(target)<4 else {'rect':target}
    if 'rect' in key: xa=target[0]; xb=target[2]
    else: xa,xb=None,None
    B=dict(key); A=dict(key)
    B['text']={l:(filler(b,size,l)+r if b else r) for l,(b,r) in texts.items()}
    A['text']={l:b for l,(b,r) in texts.items()}
    for R,w,c in ((B,'regular',GRAY),(A,'bold',boldcolor)):
        R.update(size=size,weight=w,color=c,nowrap=True)
    return B,A
regs=[]
def add(**k): regs.append(k)
add(boxes=[0],text={'es':'Calendario de puntos de control','ja':'チェックポイント・カレンダー'},size=23.5,color="#9da7b4",expand=[-36,0,250,0],nowrap=True)
add(boxes=[1],text={'es':'Fechas de EE. UU.','ja':'米国の現地日付'},size=23.5,align='right',expand=[150,0,0,5],nowrap=True)
add(boxes=[2],text={'es':'Próximas 3 semanas: ==a vigilar==','ja':'今後3週間は==この日付==に注目'},weight='black',size=63,color="#f2f5fb",accent="#ff5a5f",expand=[0,0,110,0],nowrap=True)
# month labels
MON={'es':'nov.','ja':'11月'}
for b in (3,6,9,12,19):
    add(boxes=[b],text=MON,size=21.6,color="#9aa6be",align='center',expand=[30,0,30,0],nowrap=True)
add(boxes=[16],text=MON,size=21.6,color="#3a2532",align='center',expand=[30,0,30,0],nowrap=True)
add(boxes=[22],text={'es':'hasta nov.','ja':'~11月'},size=21.6,color="#98a4bb",align='center',expand=[45,0,45,0],nowrap=True)
def ext(box_rect,right=990): return box_rect
bx={b['i']:b['rect'] for b in json.load(open('/home/claude/stayhungry-terminal/_source/rxtools/specs/ai-deleveraging-2026-11/card-en-09.boxes.json'))}
def line(i,texts,size=30,bc=WHITE):
    B,A=pair([i],texts,size,bc)
    e=[0,0,990-bx[i][2],0]
    B['expand']=e; A['expand']=e
    regs.extend([B,A])
line(4,{'es':('Road show de Anthropic',': primer día para iniciar'),'ja':('Anthropicのロードショー',' 開始が可能な最初の日')})
line(7,{'es':('5 ETF de Fidelity',': último día de negociación'),'ja':('フィデリティETF 5本',' 最終取引日')})
line(10,{'es':('Precio de IPO de Anthropic',': primer día posible'),'ja':('Anthropicの公開価格',' 決定が可能な最初の日')})
line(13,{'es':('Formularios 13F del 3T',': plazo (posiciones de SA)'),'ja':('第3四半期13F開示',' 期限（SAのポジション確認）')})
line(15,{'es':('Resultados de Nvidia',' tras el cierre en EE. UU.'),'ja':('エヌビディア決算',' 米国市場の引け後')},bc=RED)
add(boxes=[18],text={'es':'Llamada: mié. 18 de nov., 7 a. m. hora de Corea','ja':'韓国時間11/18（水）午前7時にコール'},size=23,color="#9ca7b5",expand=[0,0,300,0],nowrap=True)
line(20,{'es':('ETF de Fidelity',': fecha prevista de liquidación'),'ja':('フィデリティETF',' 清算予定日')})
# listing target: ES two lines on boxes 23/25, JA one centred line on a rect
B,A=pair([23],{'es':('Meta de salida a bolsa de Anthropic',''),'ja':('','')},30)
for R in (B,A): R['expand']=[0,0,990-bx[23][2],0]
regs.extend([B,A])
add(boxes=[25],text={'es':'(antes de Acción de Gracias; alternativa: fin de año)','ja':''},size=30,color=GRAY,expand=[0,0,990-bx[25][2],0],nowrap=True)
B,A=pair([296,1001,990,1032],{'es':('',''),'ja':('Anthropicの上場目標','（感謝祭前、代替案は年末）')},30)
regs.extend([B,A])
add(boxes=[26,27],text={'es':'Al 5 de nov., Anthropic no había presentado la enmienda con el rango de precio. Se reporta que la valuación esperada bajó de ~US$2 billones a US$1.5-1.6 billones.','ja':'Anthropicの公開価格レンジを含む修正届出書は11/5時点で未提出。評価額の期待は約2兆ドル→1.5~1.6兆ドルに下方修正と報じられた。'},size=21.5,lh=33,expand=[0,0,15,10])
add(boxes=[28],text={'es':'Fuentes: NVIDIA IR, SEC, Yahoo Finance, FinanceFeeds','ja':'出所：NVIDIA IR、SEC、Yahoo Finance、FinanceFeeds'},size=21.5,expand=[0,0,250,0],nowrap=True)
spec={"slug":"ai-deleveraging-2026-11","src":"card-en-09.webp","boxes":"card-en-09.boxes.json","langs":["es","ja"],"keep":[[78,86,113,121]],"regions":regs}
json.dump(spec,open('/home/claude/stayhungry-terminal/_source/rxtools/specs/ai-deleveraging-2026-11/card-en-09.json','w'),ensure_ascii=False,indent=1)
