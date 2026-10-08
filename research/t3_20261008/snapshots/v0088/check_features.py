import gzip,tarfile,json
from pathlib import Path
from collections import Counter
import anndata as ad
P=Path(__file__).parent;S=Path('/workspace/shared/t3_developmental_sources');panel=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad',backed='r').var_names.tolist();alias={'Wisp2':'Ccn5','Tmem2':'Cemip2'};ko=[x.split('\t') for x in gzip.open(S/'GSE137337_features.gz','rt').read().splitlines()];idmap={x[0]:alias.get(x[1],x[1]) for x in ko};out={}
t=tarfile.open(S/'admitted/GSE122187_WT_E8.5_1ab.tar.gz');mm=[a for a in t.getmembers() if a.name.endswith('genes.tsv')][0];wt=[x.split('\t') for x in t.extractfile(mm).read().decode().splitlines()]
for name,feat in [('WT',wt),('KO_shared',ko)]:
 mapped=[(x[0],x[1],idmap.get(x[0],alias.get(x[1],x[1]))) for x in feat];cnt=Counter(x[2] for x in mapped if x[2] in panel);out[name]=dict(unique=len(cnt),missing=sorted(set(panel)-set(cnt)),duplicates={g:[x for x in mapped if x[2]==g] for g,n in cnt.items() if n>1})
(P/'FEATURE_MAP_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
