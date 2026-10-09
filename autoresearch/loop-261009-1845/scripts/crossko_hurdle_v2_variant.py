"""Response-structure variant of crossko_hurdle_v2 for the winning route.

Only summarize_response changes (shrinkage lam and the global_valid mask); every
other frozen behaviour is byte-identical to the archived module. lam=15 and the
mask removal are the configuration that measured +0.1985 on the frozen local
composite (autoresearch/loop-261009-1845).

The atlas, quantiles, state assignment, support rule, composition and every
emission path are unchanged, so this is the same route with one structural
assumption swapped, not a new route.
"""
import numpy as np
from crossko_hurdle_v2 import CrossKOHurdle as _Base


class CrossKOHurdleVariant(_Base):
    LAM = 15.0
    USE_MASK = False

    def summarize_response(self, control, ko):
        from crossko import closed

        closed(control)
        closed(ko)
        cl = self.assign(control)
        kl = self.assign(ko)
        nc = np.bincount(cl, minlength=self.S)
        nk = np.bincount(kl, minlength=self.S)
        zero = np.zeros((self.G, len(self.positive_q)))
        cq, cv = self.positive_quantiles(control, zero)
        kq, kv = self.positive_quantiles(ko, cq)
        global_delta = kq - cq
        global_detect = (ko > 0).mean(0) - (control > 0).mean(0)
        global_valid = cv & kv

        result = []
        supports = []
        for s in range(self.S):
            supported = nc[s] >= self.min_cells and nk[s] >= self.min_cells
            supports.append(supported)
            if not supported:
                result.append(np.zeros((self.G, len(self.q))))
                continue
            a = control[cl == s]
            b = ko[kl == s]
            aq, _ = self.positive_quantiles(a, cq)
            bq, _ = self.positive_quantiles(b, kq)
            lam = nk[s] / (nk[s] + self.LAM)
            d = lam * (bq - aq) + (1 - lam) * global_delta
            rate = lam * ((b > 0).mean(0) - (a > 0).mean(0)) + (1 - lam) * global_detect
            if self.USE_MASK:
                d[~global_valid] = 0
                rate[~global_valid] = 0
            result.append(np.c_[d, rate])
        comp = np.log((nk + 0.5) / (nk.sum() + 0.5 * self.S)) - np.log(
            (nc + 0.5) / (nc.sum() + 0.5 * self.S)
        )
        comp = comp - comp.mean()
        return dict(delta=np.array(result), composition=comp, support=np.array(supports))