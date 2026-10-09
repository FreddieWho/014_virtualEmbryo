"""Fidelity check: does the recomputed frozen response match the original cache?"""
import numpy as np

a = np.load("/home/huyudi/vework/responses/frozen.npz")
b = np.load("/home/huyudi/vework/eval/baseline_reference/embryo_responses.npz")

ok = True
for k in ["delta", "composition", "support"]:
    x, y = a[k], b[k]
    same = x.shape == y.shape and np.array_equal(x, y)
    ok &= same
    extra = ""
    if x.shape == y.shape:
        diff = np.abs(x.astype(float) - y.astype(float)).max()
        extra = f" maxabs={diff:.3e}"
    print(f"{k:12} shapes {x.shape} vs {y.shape} exact={same}{extra}")
print("HARNESS_FIDELITY", "PASS" if ok else "FAIL")