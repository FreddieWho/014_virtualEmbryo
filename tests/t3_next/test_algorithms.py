import numpy as np
import pytest
from scripts.t3_next.algorithms import rank_rebuild, residual_counterfactual, donor_replace, signal_delta, gene_split, forbidden_perturbation, fit_graph_comparator


def test_rank_preserves_columns_and_identity():
    wt=np.array([[3,1,0],[1,3,0],[2,2,0]],dtype=float)
    donor=np.array([[8,4,0],[7,9,0],[6,5,0]],dtype=float)
    out=rank_rebuild(wt,donor,2)
    np.testing.assert_array_equal(np.sort(out,axis=0),np.sort(donor,axis=0))
    np.testing.assert_array_equal(out[:,0],[8,6,7])
    np.testing.assert_array_equal(rank_rebuild(wt,wt,2),wt)


def test_counterfactual_preserves_individual_residual_and_chain():
    x=np.array([[1.,3.,10.],[2.,5.,15.]])
    models={1:([0],lambda a: 2*a[:,0]),2:([1],lambda a: 3*a[:,0])}
    np.testing.assert_array_equal(residual_counterfactual(x,models,0,None),x)
    cf=residual_counterfactual(x,models,0,0.)
    np.testing.assert_allclose(cf,[[0,1,4],[0,1,3]])


def test_donor_replace_is_whole_cell_with_stratum_guard():
    x=np.arange(12).reshape(4,3).astype(float)
    out=donor_replace(x,np.array([0,1]),np.array([2,3]),np.array(['a','b','a','b']),target_col=1)
    np.testing.assert_array_equal(out[0,[0,2]],x[2,[0,2]])
    with pytest.raises(ValueError):donor_replace(x,np.array([0]),np.array([1]),np.array(['a','b','a','b']),target_col=1)


def test_neighbor_propagates_delta_only_not_expression():
    from scipy.sparse import csr_matrix
    w=csr_matrix(np.array([[0,1],[1,0]],float));x=np.array([[2,3,4],[1,5,2]],float)
    assert not signal_delta(x,np.zeros_like(x),w,[(0,1,2,0.2)]).any()
    d=np.zeros_like(x);d[0,0]=-1
    out=signal_delta(x,d,w,[(0,1,2,0.2)])
    assert out[0,2]==0 and out[1,2]<0
    assert np.count_nonzero(out)==1


def test_gene_split_and_blacklist_cover_combinations():
    assert forbidden_perturbation('safe+GATA4')
    assert forbidden_perturbation('ctnnb1')
    assert forbidden_perturbation('NKX2-5+ctrl')
    assert not forbidden_perturbation('Mab21l2')
    train,test=gene_split([f'Gene{i}' for i in range(30)],seed=1)
    assert not set(train)&set(test) and len(test)==6


def test_graph_model_actually_trains_on_synthetic_gene_holdout():
    rng=np.random.default_rng(5);emb=rng.normal(size=(30,5)).astype('float32');effects=emb@rng.normal(size=(5,4)).astype('float32')
    out=fit_graph_comparator(emb,effects,np.eye(30,dtype='float32'),np.arange(24),np.arange(24,30),epochs=4,seed=1)
    assert out['training_steps']==4
    assert out['graph_prediction'].shape==(6,4)
    assert np.isfinite(out['graph_prediction']).all()
    assert out['train_test_gene_overlap']==0


def test_conditional_models_identity_and_bounded_extrapolation():
    from scripts.t3_next.routes_local import ConditionalModel
    rng=np.random.default_rng(8);p=rng.uniform(1,3,(80,2));z=rng.normal(size=(80,2));t=np.array(['a','b']*40);y=p[:,0]+z[:,0]
    model=ConditionalModel('bounded_spline').fit(p,z,t,y)
    lower=np.min(p,0)[None,:].repeat(80,axis=0)
    np.testing.assert_allclose(model.predict(np.zeros_like(p),z,t),model.predict(lower,z,t))


def test_dag_layering_explicitly_drops_cycles():
    import pandas as pd
    from scripts.t3_next.routes_local import graph_from_motif
    motif=pd.DataFrame({'gene_short_name':['A','B','Gata4'],'Gata4':[1,0,0],'A':[0,1,0],'B':[1,0,1]})
    parents,dropped=graph_from_motif(motif,['Gata4','A','B'])
    assert parents=={1:[0],2:[1]}
    assert any(r['source']=='B' and r['target']=='Gata4' for r in dropped)


def test_random_control_cannot_replace_a_cell_with_itself_or_identical_profile():
    from scripts.t3_next.algorithms import distinct_donor_map
    x=np.array([[1,0,3],[1,9,3],[4,2,6]],float)
    result=distinct_donor_map(np.array([0]),np.array([0,1,2]),np.array([[0,.1,.2]]),np.array([[0,1,2]]),x,1,1.)
    assert result=={0:2}


def test_crossmodal_mapping_does_not_use_heldout_genes_or_cross_groups():
    from scripts.t3_next.routes_extended import mapped_neighbors
    rng=np.random.default_rng(7);rna=rng.normal(size=(60,5)).astype('float32');wt=rng.normal(size=(50,3)).astype('float32')
    ag=np.array(['a']*30+['b']*30);wg=np.array(['a']*25+['b']*25);mask=np.ones(50,bool)
    idx,_,_=mapped_neighbors(rna,wt,ag,wg,[0,1],mask,2,3,4)
    changed=rna.copy();changed[:,2]=rng.normal(size=60)*1000
    idx2,_,_=mapped_neighbors(changed,wt,ag,wg,[0,1],mask,2,3,4)
    np.testing.assert_array_equal(idx,idx2)
    assert np.all(ag[idx]==wg[:,None])


@pytest.mark.parametrize('kind',['linear','bounded_spline'])
def test_grouped_ridge_is_equivalent_to_individual_gene_fits(kind):
    from scripts.t3_next.routes_local import ConditionalModel
    rng=np.random.default_rng(33);p=rng.normal(size=(150,3));z=rng.normal(size=(150,2));t=np.array(['a','b','c']*50);y=rng.normal(size=(150,4))
    multi=ConditionalModel(kind).fit(p,z,t,y).predict(p,z,t)
    singles=np.column_stack([ConditionalModel(kind).fit(p,z,t,y[:,j]).predict(p,z,t) for j in range(4)])
    np.testing.assert_allclose(multi,singles,atol=1e-9,rtol=1e-9)
