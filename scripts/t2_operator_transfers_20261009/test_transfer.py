import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']:
    os.environ[k]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'repo/scripts/t2_embryo_campaign_20261009'))
import unittest,numpy as np
from copula import fit_conditional,regularize
class Tests(unittest.TestCase):
    def test_exact_marginals_replay_small_states_zeros(self):
        rng=np.random.default_rng(921)
        X=rng.poisson(1,(103,500)).astype('float32');X[:,0]=0
        labels=np.array(['a']*50+['b']*50+['small']*3)
        B,fit=fit_conditional(rng.poisson(2,(205,500)))
        Y,info=regularize(X,labels,B);Z,_=regularize(X,labels,B)
        np.testing.assert_array_equal(Y,Z)
        np.testing.assert_array_equal(X[100:],Y[100:])
        np.testing.assert_array_equal(Y[:,0],0)
        for s in set(labels):np.testing.assert_array_equal(np.sort(X[labels==s],axis=0),np.sort(Y[labels==s],axis=0))
        self.assertTrue(np.isfinite(Y).all());self.assertEqual(fit['blend'],.5);self.assertFalse(fit['parameter_search'])
    def test_gene_shuffle_spectrum_and_values(self):
        rng=np.random.default_rng(928);lat=rng.normal(size=(200,3));X=lat@rng.normal(size=(3,40))+.2*rng.normal(size=(200,40));B,_=fit_conditional(X)
        p=rng.permutation(40);S=B[np.ix_(p,p)]
        np.testing.assert_array_equal(np.sort(B.ravel()),np.sort(S.ravel()))
        np.testing.assert_allclose(np.sort(np.linalg.eigvals(B)),np.sort(np.linalg.eigvals(S)),atol=1e-12)
        self.assertFalse(np.array_equal(B,S))
    def test_design_no_embryo_data_and_no_target_fit(self):
        import json
        d=json.loads((Path(__file__).parent/'DESIGN.json').read_text())
        self.assertEqual(d['fit_stages_final'],['E8.25_late','E8.75'])
        self.assertNotIn(d['evaluation_stage_strict_holdout'],d['fit_stages_strict_holdout'])
        self.assertFalse(d['embryo_fitted_B_reuse']);self.assertFalse(d['protected_target_access'])
        self.assertEqual(d['numerical_threads'],1);self.assertEqual(d['num_candidates_max'],1)
if __name__=='__main__':unittest.main()
