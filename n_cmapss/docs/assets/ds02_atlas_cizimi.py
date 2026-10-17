from pathlib import Path
import tempfile,os
os.environ['MPLCONFIGDIR']=str(Path(tempfile.gettempdir())/'n_cmapss_matplotlib_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle,FancyArrowPatch,PathPatch,FancyBboxPatch
from matplotlib.path import Path as MPath
import numpy as np
assets=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','font.size':11})
blue='#1261a0';purple='#8547ad';green='#187b60';ink='#193047';light='#eef3f7';orange='#dd6b20'
fig,ax=plt.subplots(figsize=(24,15));fig.subplots_adjust(left=.015,right=.985,bottom=.015,top=.985)
ax.set(xlim=(0,24),ylim=(0,16));ax.set_aspect('equal');ax.axis('off')
ax.text(.45,15.55,'DS02 • TURBOFAN MOTOR VE ÖLÇÜM İSTASYONLARI',fontsize=23,weight='bold',color=ink)
ax.text(.45,15.02,'Özgün, temsili teknik kesit • akış soldan sağa • geometri / kademe sayıları ölçekli CMAPSS tasarımı değildir',fontsize=12,color=ink)
# Nacelle/casing: temsilî simetrik duvarlar, bypass ve çekirdek kanalı.
outer=[(1.5,10.95),(2.3,11.4),(4.2,11.5),(7.5,11.05),(17.4,10.65),(21.8,9.95),(22.7,9.55),(22.0,9.25),(17.3,10.2),(7.5,10.6),(4.1,11.0),(2.5,10.95),(1.5,10.65)]
ax.add_patch(Polygon(outer,closed=True,facecolor='#b8c6d2',edgecolor=ink,lw=1.5))
ax.add_patch(Polygon([(x,17.4-y) for x,y in outer],closed=True,facecolor='#b8c6d2',edgecolor=ink,lw=1.5))
coretop=[(4.4,9.85),(6.8,9.65),(10.5,9.5),(11,9.95),(13.2,9.95),(13.9,9.75),(16,9.8),(18.8,9.65),(20.8,9.2),(20.5,9.0),(18.6,9.4),(16,9.55),(13.9,9.5),(13.1,9.7),(11.2,9.7),(10.5,9.28),(6.8,9.4),(4.4,9.6)]
ax.add_patch(Polygon(coretop,closed=True,facecolor='#758a9e',edgecolor=ink,lw=1.2))
ax.add_patch(Polygon([(x,17.4-y) for x,y in coretop],closed=True,facecolor='#758a9e',edgecolor=ink,lw=1.2))
# Arkadaki nozül ve akış gölgeleri.
ax.add_patch(Polygon([(18.2,9.25),(21.5,9.0),(22.8,8.7),(21.5,8.4),(18.2,8.15)],facecolor='#e5ebf0',edgecolor=ink,lw=1))
ax.add_patch(Polygon([(2,9.25),(5.1,9.45),(10.4,9.25),(11,9.6),(13,9.6),(15,9.4),(18.6,9.3),(21.5,8.95),(21.5,8.45),(18.6,8.1),(15,8.0),(13,7.8),(11,7.8),(10.4,8.15),(5.1,7.95),(2,8.15)],facecolor='#fff1dc',edgecolor='none',alpha=.8))
# Fan diski ve giriş konisi.
ax.add_patch(Polygon([(1.6,8.7),(2.8,9.05),(4.5,9.0),(5.2,8.7),(4.5,8.4),(2.8,8.35)],facecolor='#627d91',edgecolor=ink,lw=1.5))
for sign in [-1,1]:
 ax.add_patch(Polygon([(3.35,8.7),(3.55,8.7+sign*2.26),(3.86,8.7+sign*2.15),(3.85,8.7)],facecolor='#acbdca',edgecolor=ink,lw=1))
 for k in range(5):
  y=8.7+sign*(.5+.32*k)
  ax.plot([3.55,3.79],[y,y+sign*.1],color='white',lw=.8)
# Mil/rotor geometrisi: düşük/yüksek basınç milleri ayrı görünür.
ax.add_patch(Rectangle((3.4,8.59),14.5,.22,facecolor='#405d75',edgecolor=ink,lw=.7))
ax.add_patch(Rectangle((6.9,8.77),7.6,.10,facecolor='#8d6e50',edgecolor=ink,lw=.7))
# Kompresör kademe kanatları: nicel olmayan temsil.
for x,height in [(4.8,.9),(5.45,.85),(6.1,.8),(7.1,.73),(7.65,.69),(8.2,.65),(8.75,.61),(9.3,.57),(9.85,.54)]:
 for sign in [-1,1]:
  ax.add_patch(Polygon([(x,8.7),(x+.12,8.7+sign*height),(x+.32,8.7+sign*(height-.04)),(x+.30,8.7)],facecolor='#8aa7bb',edgecolor=ink,lw=.65))
  ax.plot([x+.44,x+.38],[8.7+sign*.35,8.7+sign*(height+.05)],color='#536f83',lw=2)
# Yanma odası: iki annüler kesit, alevler ve yakıt besleme hattı.
for sign in [-1,1]:
 y=9.0 if sign==1 else 7.9
 ax.add_patch(FancyBboxPatch((10.8,y),2.45,.52,boxstyle='round,pad=.02,rounding_size=.12',facecolor='#f4c27f',edgecolor='#9c5122',lw=1.3))
 for i in range(4):
  x=11.08+i*.47
  ax.add_patch(Polygon([(x,y+.13),(x+.32,y+.30),(x+.15,y+.39),(x+.47,y+.26)],facecolor='#e56f24',edgecolor='none'))
ax.plot([11.25,11.25,12.2],[9.58,10.18,10.18],color='#964b23',lw=2)
ax.text(12.3,10.2,'Yakıt sistemi / fuel system\nWf: debi, tek bir gaz istasyonu değil',fontsize=8.8,color=blue,va='center')
# Türbin diskleri ve statorlar.
for x,height,color in [(13.65,.83,'#b9825a'),(14.3,.86,'#b9825a'),(15.5,.95,'#9d9b8e'),(16.2,1.0,'#9d9b8e'),(16.9,1.03,'#9d9b8e'),(17.6,1.06,'#9d9b8e')]:
 for sign in [-1,1]:
  ax.add_patch(Polygon([(x,8.7),(x+.05,8.7+sign*height),(x+.27,8.7+sign*(height-.03)),(x+.31,8.7)],facecolor=color,edgecolor=ink,lw=.7))
  ax.plot([x+.42,x+.47],[8.7+sign*.3,8.7+sign*(height+.03)],color='#7c6d5d',lw=1.6)
# Bölüm adları motorun altında ayrı, okunaklı bantta.
components=[(3.6,'Fan','Fan'),(5.55,'LPC','Alçak basınç kompresörü\nLow-pressure compressor'),(8.55,'HPC','Yüksek basınç kompresörü\nHigh-pressure compressor'),(12,'Combustor','Yanma odası'),(14.1,'HPT','Yüksek basınç türbini\nHigh-pressure turbine'),(16.7,'LPT','Alçak basınç türbini\nLow-pressure turbine')]
for x,en,tr in components:
 ax.text(x,6.1,en,ha='center',fontsize=12,weight='bold',color=ink)
 ax.text(x,5.68,tr,ha='center',fontsize=8,color=ink,va='top')
# Akış okları bypass ve çekirdekte.
for y,color in [(10.35,green),(7.7,orange),(7.05,green)]:
 for start,end in [(1.0,2.7),(5.0,7.0),(8.3,10.1),(15.6,18.3),(20.7,23.1)]:
  ax.add_patch(FancyArrowPatch((start,y),(end,y),arrowstyle='-|>',mutation_scale=14,lw=1.4,color=color,alpha=.8))
ax.text(19,10.65,'BYPASS / ÇEKİRDEK DIŞI AKIŞ',fontsize=8.5,color=green,ha='center')
# Gruplar: ölçülebilir mavi, model mor, W yeşil. Oklar bölgeyi gösterir, prob yerleşimi değildir.
def callout(text,xy,xytext,color,size=11):
 ax.annotate(text,xy=xy,xytext=xytext,ha='center',va='center',fontsize=size,color=color,
   bbox=dict(boxstyle='round,pad=.35',fc='white',ec=color,lw=1.2),
   arrowprops=dict(arrowstyle='->',color=color,lw=1.05,connectionstyle='angle3,angleA=90,angleB=0'),zorder=20)
callout('T2 (W, °R)',(2.3,9.45),(1.55,13.7),green)
callout('P2 (X_s, psia)',(2.4,9.10),(1.55,12.55),blue,10)
callout('T24 (°R)\nLPC çıkışı',(6.7,9.3),(5.5,13.65),blue)
callout('T30 (°R)\nHPC çıkışı',(10.4,9.1),(9.0,13.65),blue)
callout('T40 (°R)\nYanma odası çıkışı',(13.25,9.36),(12.6,13.65),purple)
callout('T48 (°R)\nHPT çıkışı',(15.0,9.25),(16.3,13.65),blue)
callout('T50 (°R)\nLPT çıkışı',(18.5,9.2),(20.65,13.65),blue)
callout('P15 (psia)\nBypass kanalı',(7.6,10.3),(21.65,11.65),blue,10)
# Basınçların alt taraftaki bölgesel bağlantıları.
for text,xy,xytext,col in [
 ('P21 (psia)\nFan çıkışı',(4.45,8.05),(3.15,4.55),blue),
 ('P24 (psia)\nLPC çıkışı',(6.7,8.1),(6.05,4.55),blue),
 ('Ps30 (psia)\nHPC çıkışı: statik',(10.35,8.15),(8.6,4.55),blue),
 ('P30 (psia)\nHPC çıkışı: toplam',(10.35,8.3),(10.5,3.55),purple),
 ('P40 (psia)\nCombustor çıkışı / HPT girişi',(13.25,8.0),(13.2,4.55),blue),
 ('P45 (psia)\nHPT çıkışı',(15,8.1),(16.5,4.55),purple),
 ('P50 (psia)\nLPT çıkışı',(18.5,8.2),(20.0,4.55),blue)]:callout(text,xy,xytext,col,9.5)
# Statik Ps30 fiziksel mavi anlamını aynı kutu içinde belirginleştir.
# Bileşen/sistem büyüklükleri noktasal prob işaretiyle gösterilmez.
cards=[(.5,'MİLLER / SHAFT SYSTEM', 'Nf (X_s, rpm): fan / düşük basınç mili\nNc (X_s, rpm): çekirdek / yüksek basınç mili',blue),
 (6.4,'AKIŞ VE SOĞUTMA / FLOW', 'W21, W22, W25: fan–kompresör akışları\nW31/W32: HPT soğutma; kademe belirsiz\nW48/W50: türbin çıkış akışları (lbm/s)',purple),
 (12.3,'KARARLILIK / STALL MARGIN','SmFan, SmLPC, SmHPC: bileşen rezervleri\nSanal/model çıktısı; tek nokta probu değil\nKaynak birimi: boyutsuz, sağlık % değil',purple),
 (18.2,'ORAN / MODEL ÇIKTISI','phi: yakıt–Ps30 ilişkisi (kaynak tanımı)\npps/psi; dosyadaki ölçek belirsiz\nTek nokta sensörü / fuel–air ratio değil',purple)]
for x,title,body,col in cards:
 ax.add_patch(FancyBboxPatch((x,.72),5.35,2.3,boxstyle='round,pad=.12',facecolor='#f7f9fb',edgecolor=col,lw=1.1))
 ax.text(x+.16,2.66,title,fontsize=10,weight='bold',color=col)
 ax.text(x+.16,2.16,body,fontsize=9.2,va='top',linespacing=1.65,color=ink)
ax.text(.5,.23,'RENK: mavi = X_s fiziksel ölçülebilir • mor = X_v sanal/model • yeşil = W koşulu. Kaynak: Arias Chao vd. (2021), Tables 4–6 / Fig.2.',fontsize=10,color=ink)
for ext in ['svg','png']:fig.savefig(assets/f'ds02_turbofan_kesit.{ext}',dpi=140,facecolor='white')
plt.close(fig)
# Ayrı akış sistemleri çizimi: doğrulanamayan ince devreler kesikli çizilir.
fig,ax=plt.subplots(figsize=(20,7));fig.subplots_adjust(left=.02,right=.98,bottom=.03,top=.97)
ax.set(xlim=(0,20),ylim=(0,7));ax.axis('off')
ax.text(.2,6.5,'AKIŞLAR BİR NOKTA SENSÖRÜ DEĞİL, MOTORUN AKIŞ YOLLARIDIR',fontsize=18,weight='bold',color=ink)
ax.text(.2,6,'Özgün öğretici şema • Table 6 bölge tanımları • dallanma / soğutma kademe ayrıntısı temsili',fontsize=11,color=ink)
blocks=[(.8,'Fan'),(4.1,'LPC'),(7.4,'HPC'),(10.7,'Combustor'),(14.0,'HPT'),(17.3,'LPT')]
for x,name in blocks:
 ax.add_patch(FancyBboxPatch((x,3.1),2.1,1.2,boxstyle='round,pad=.1',facecolor=light,edgecolor=ink,lw=1.2))
 ax.text(x+1.05,3.7,name,ha='center',va='center',fontsize=13,color=ink)
for (x,_),(nx,_) in zip(blocks,blocks[1:]):
 ax.add_patch(FancyArrowPatch((x+2.2,3.7),(nx-.12,3.7),arrowstyle='-|>',mutation_scale=15,color=green,lw=2))
for x,txt in [(1.85,'W21\nFan debisi'),(5.15,'W22\nLPC çıkışı'),(8.45,'W25\nHPC girişi'),(15.05,'W48\nHPT çıkışı'),(18.35,'W50\nLPT çıkışı')]:
 ax.text(x,2.55,txt,ha='center',va='top',color=purple,fontsize=11)
 ax.plot([x,x],[3.0,2.7],color=purple,lw=1)
ax.add_patch(FancyArrowPatch((8.5,4.5),(15.0,4.5),arrowstyle='-|>',mutation_scale=15,color=purple,lw=2,linestyle='--',connectionstyle='arc3,rad=-.35'))
ax.text(11.7,1.65,'W31 / W32: HPT soğutma bleed akışları\nAyrı kanallar; tam kademe/devre eşleştirmesi doğrulanmadı',ha='center',color=purple,fontsize=10.5)
ax.add_patch(FancyArrowPatch((2.0,4.5),(19.8,5.1),arrowstyle='-|>',mutation_scale=12,color=green,lw=1.3,linestyle=':',connectionstyle='arc3,rad=-.13'))
ax.text(3.0,5.2,'Bypass yolu (temsili)',color=green,fontsize=10)
ax.text(.4,.8,'W21: kaynakta pps; diğer W akışları lbm/s. Hepsi kütlesel debi; veri/birim dönüşümü uygulanmaz.\nW22 ve W25 konumları Table 6 metnine göre adlandırıldı; yakın fiziksel bölgeler farklı model değişkenleridir.',fontsize=11,color=ink,linespacing=1.6)
for ext in ['svg','png']:fig.savefig(assets/f'ds02_akis_sistemleri.{ext}',dpi=140,facecolor='white')
plt.close(fig)
print('Generated original SVG/PNG engineering schematics:',assets)
