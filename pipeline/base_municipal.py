"""Monta a tabela municipal unificada (1 linha por município do CE).

Uso (da raiz do projeto):  python pipeline/base_municipal.py <PASTA_OBITOS>
<PASTA_OBITOS> tem cases_2020/2021/2022.csv.gz (não ficam no repositório; ver docs/06).
Grava dados/processados/municipal.csv.
"""
import sys, json, csv, io, numpy as np, pandas as pd
from shapely.geometry import shape
EXT = sys.argv[1]
REPO = "dados/brutos"
OUT = "dados/processados/municipal.csv"

def sidra(path, valname):
    rows=[]
    for r in csv.reader(open(path, encoding='utf-8-sig'), delimiter=';'):
        if len(r)>=5 and r[0]=='MU' and r[1].isdigit():
            rows.append((r[1], r[-2]))
    d=pd.DataFrame(rows, columns=['ibge',valname])
    d[valname]=pd.to_numeric(d[valname].str.replace('.','',regex=False).str.replace(',','.',regex=False), errors='coerce')
    return d

# --- vacinação
v=pd.read_csv(f"{REPO}/vacinacao/processed_CE.csv.gz", dtype={'ibgeID':str})
v=v.rename(columns={'ibgeID':'ibge'})
pop21=v.groupby('ibge').pop2021.first()
def cum(df, cutoff=None):
    d=df if cutoff is None else df[df.date<=cutoff]
    t=d.pivot_table(index='ibge',columns='dose',values='count',aggfunc='sum',fill_value=0)
    return t.reindex(columns=[0,1,2,3],fill_value=0)
M=pd.DataFrame({'pop2021':pop21})
for tag,cut in [('jun21','2021-06-30'),('dez21','2021-12-31'),('dez22','2022-12-31'),('fim',None)]:
    t=cum(v,cut)
    M[f'd1_{tag}']=t[1]+t[0]; M[f'comp_{tag}']=t[2]+t[0]; M[f'ref_{tag}']=t[3]
# idosos 60+
old=v[v.age.isin(['60-64','65-69','70-74','75-79','80-84','85-89','90+'])]
to=cum(old,'2021-12-31'); M['comp60_dez21']=to[2]+to[0]; M['d1_60_dez21']=to[1]+to[0]
# dia em que a 1ª dose (D1+DU) chegou a 50% da pop 2021
dd=v[v.dose.isin([0,1])].groupby(['ibge','date'])['count'].sum().groupby(level=0).cumsum().reset_index()
dd=dd.merge(pop21.rename('p').reset_index(),on='ibge')
first=dd[dd['count']>=0.5*dd.p].groupby('ibge').date.min()
M['dia_d1_50']=(pd.to_datetime(first)-pd.Timestamp('2021-01-17')).dt.days
M=M.reset_index()

# --- nomes e IDHM da base original (recalculando as coberturas a partir dos dados brutos)
b=pd.read_csv(f"{REPO}/referencia/municipios.csv", dtype={'ibge':str})
M=M.merge(b[['ibge','municipio','capital','idhm','idhm_renda','idhm_longevidade','idhm_educacao']],on='ibge',how='left')

# --- Censo 2022
M=M.merge(sidra(f"{REPO}/ibge/tabela9923.csv",'pop2022'),on='ibge',how='left')
M=M.merge(sidra(f"{REPO}/ibge/tabela10061.csv",'pop18_2022'),on='ibge',how='left')
M=M.merge(sidra(f"{REPO}/ibge/tabela9543.csv",'alfab15'),on='ibge',how='left')

# --- influenza 2019 (cabeçalho ausente; grupos identificados pela magnitude)
fl=pd.read_csv(f"{REPO}/vacinacao/coberturaVacinalInfluenza_2019.csv",header=None,dtype=str,encoding='latin1')
fl=fl[fl[4]=='CE'].copy()
num=lambda s: pd.to_numeric(s.str.replace('.','',regex=False).str.replace(',','.',regex=False),errors='coerce')
fl['ibge6']=fl[2]; fl['flu_idosos_pop']=num(fl[24]); fl['flu_idosos_doses']=num(fl[25]); fl['flu_idosos_cob']=num(fl[26])/100
fl['flu_total_cob']=num(fl[35])/100; fl['flu_criancas_cob']=num(fl[13])/100
M['ibge6']=M.ibge.str[:6]
M=M.merge(fl[['ibge6','flu_idosos_pop','flu_idosos_doses','flu_idosos_cob','flu_total_cob','flu_criancas_cob']],on='ibge6',how='left')

# --- óbitos (covid19br)
def deaths_at(year, date):
    c=pd.read_csv(f"{EXT}/cases_{year}.csv.gz",usecols=['date','state','ibgeID','deaths'],dtype={'ibgeID':str})
    c=c[(c.state=='CE')&(c.date<=date)]
    return c.sort_values('date').groupby('ibgeID').deaths.last()
d20=deaths_at(2020,'2020-12-31'); d21=deaths_at(2021,'2021-12-31'); d22=deaths_at(2022,'2022-12-31')
M['obitos_2020']=M.ibge.map(d20).fillna(0); M['obitos_ate21']=M.ibge.map(d21).fillna(0); M['obitos_ate22']=M.ibge.map(d22).fillna(0)

# --- geografia
g=json.load(open(f"{REPO}/referencia/geojs-23-mun.json"))
geo={f['properties']['id']:shape(f['geometry']) for f in g['features']}
# área aproximada em km² (projeção equiretangular local)
lat0=np.deg2rad(-5.2); kx=111.32*np.cos(lat0); ky=110.57
from shapely.affinity import scale
M['area_km2']=M.ibge.map(lambda i: scale(geo[i],xfact=kx,yfact=ky,origin=(0,0)).area)
fz=geo['2304400'].centroid
M['dist_fortaleza_km']=M.ibge.map(lambda i: ((geo[i].centroid.x-fz.x)*kx)**2+((geo[i].centroid.y-fz.y)*ky)**2).pow(.5)
ids=list(geo); 
nb={i:[j for j in ids if j!=i and geo[i].buffer(1e-4).intersects(geo[j])] for i in ids}
M['vizinhos']=M.ibge.map(lambda i: ';'.join(nb[i]))

# --- indicadores
P=M.pop2021; C=M.pop2022
for tag in ['jun21','dez21','dez22','fim']:
    M[f'cob_d1_{tag}']=M[f'd1_{tag}']/P; M[f'cob_comp_{tag}']=M[f'comp_{tag}']/P
M['cob_comp_fim_censo']=M.comp_fim/C; M['cob_d1_fim_censo']=M.d1_fim/C
M['cob_ref_fim']=M.ref_fim/P
M['abandono_fim']=1-M.comp_fim/M.d1_fim
M['cob_comp60_dez21']=M.comp60_dez21/M.flu_idosos_pop
M['razao_pop22_21']=C/P
M['densidade']=C/M.area_km2
M['mort20_100k']=M.obitos_2020/P*1e5
M['mort21_100k']=(M.obitos_ate21-M.obitos_2020)/P*1e5
M['alerta']=(M.cob_d1_fim>1)|(M.cob_comp_fim>1)|(M.abandono_fim<0)
M.to_csv(OUT,index=False)
print(M.shape, M.municipio.isna().sum(), M[['pop2022','alfab15','flu_idosos_cob','obitos_2020']].isna().sum().to_dict())
