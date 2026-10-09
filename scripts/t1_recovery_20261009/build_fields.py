import os
import sys,pickle,json
from pathlib import Path
import anndata as ad
ROOT=Path(os.environ.get("T1_RECOVERY_ROOT", "t1_recovery_run"))
sys.path.insert(0,str(ROOT/"vework/t1ext"))
import anchor as A,otfield as O
A.set_inext(ad.read_h5ad(ROOT/"ext/proc/GSM7226272_E14_5_1.h5ad",backed="r").var["in_external"].values)
fields=O.build_fields(log=lambda m:print(m,flush=True))
(ROOT/"work/t1r3/fields_14.5.pkl").write_bytes(pickle.dumps(fields,protocol=5))
(ROOT/"work/t1r3/FIELDS_DIAG.json").write_text(json.dumps({g:F["diag"] for g,F in fields.items()},indent=2))
