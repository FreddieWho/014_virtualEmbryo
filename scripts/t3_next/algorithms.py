"""Array-level mechanisms, with no filesystem/network or target-score access."""
from __future__ import annotations
import re
import numpy as np
from sklearn.linear_model import Ridge


def rank_rebuild(wt, donor, target_col):
    wt=np.asarray(wt); donor=np.asarray(donor)
    if wt.shape!=donor.shape: raise ValueError('WT/donor shape mismatch')
    out=donor.copy()
    for j in range(wt.shape[1]):
        if j==target_col: continue
        order=np.argsort(wt[:,j],kind='stable')
        out[order,j]=np.sort(donor[:,j],kind='stable')
    return out


def residual_counterfactual(x, models, target_col, value):
    """models is topologically ordered; preserve each observed unit's residual."""
    x=np.asarray(x); out=x.copy()
    if value is None: return out
    out[:,target_col]=value
    for node,(parents,predict) in models.items():
        out[:,node]=x[:,node]+predict(out[:,parents])-predict(x[:,parents])
    return out


def donor_replace(x, recipients, donors, strata, target_col):
    if len(recipients)!=len(donors):raise ValueError('mapping length mismatch')
    if not np.array_equal(strata[recipients],strata[donors]):raise ValueError('cross-stratum donor')
    out=np.asarray(x).copy();out[recipients]=x[donors];out[:,target_col]=0
    return out


def distinct_donor_map(targets, donors, distances, neighbors, values, target_col, radius):
    """Exclude self/identical profiles so matched replacement counts are real."""
    keep=np.arange(values.shape[1])!=target_col
    result={}
    for recipient,ds,ns in zip(targets,distances,neighbors):
        for distance,neighbor in zip(np.atleast_1d(ds),np.atleast_1d(ns)):
            if distance>radius:break
            donor=int(donors[neighbor])
            if donor!=recipient and not np.array_equal(values[int(recipient),keep],values[donor,keep]):
                result[int(recipient)]=donor;break
    return result


def signal_delta(x, intrinsic_delta, adjacency, edges):
    """Only the ligand intervention is spatially transported, never basal X."""
    out=np.zeros_like(x,dtype=float)
    for ligand,receptor,target,coef in edges:
        signal=adjacency@intrinsic_delta[:,ligand]
        gate=x[:,receptor]/max(float(np.mean(x[:,receptor])),1e-8)
        out[:,target]+=float(coef)*signal*gate
    return out


FORBIDDEN={'GATA4','GATA6','CTNNB1','MESP1','GATA1','GATA2','GATA3','GATA5','APC','AXIN1','AXIN2','GSK3A','GSK3B','DVL1','DVL2','DVL3','LRP5','LRP6','TCF7L1','TCF7L2','LEF1','NKX2-5','NKX2_5','NKX25','TBX5','MEF2C','HAND1','HAND2','ISL1'}

def forbidden_perturbation(condition):
    words=re.split(r'[+;,| /]+',str(condition).upper())
    return any(w in FORBIDDEN for w in words) or bool(re.search(r'BETA.?CATENIN|CANONICAL.?WNT',str(condition).upper()))


def gene_split(genes,seed=20260920,fraction=0.2):
    genes=np.array(sorted(set(genes)));rng=np.random.default_rng(seed)
    order=rng.permutation(len(genes));n=max(1,int(np.ceil(len(genes)*fraction)))
    return genes[order[n:]].tolist(),genes[order[:n]].tolist()


def fit_graph_comparator(embedding,effects,adjacency,train,test,epochs=100,seed=20260920):
    """Train a small explicit GCN comparator (not a claimed GEARS reproduction).

    Graph/embeddings must be outcome-free for held-out perturbations. Only train
    effect rows enter the loss. Each row is one distinct perturbation gene.
    """
    import torch
    torch.set_num_threads(8);torch.manual_seed(seed)
    train=np.asarray(train);test=np.asarray(test)
    if set(train)&set(test):raise ValueError('perturbation gene leakage')
    z=np.asarray(embedding,dtype=np.float32);y=np.asarray(effects,dtype=np.float32)
    mu=z[train].mean(0);sd=np.maximum(z[train].std(0),1e-4);z=(z-mu)/sd
    a=np.asarray(adjacency,dtype=np.float32)+np.eye(len(z),dtype=np.float32)
    a=a/np.maximum(a.sum(1,keepdims=True),1e-8)
    zt=torch.from_numpy(z);at=torch.from_numpy(a);yt=torch.from_numpy(y)
    h=torch.nn.Linear(z.shape[1],32);out=torch.nn.Linear(32,y.shape[1])
    opt=torch.optim.Adam(list(h.parameters())+list(out.parameters()),lr=0.01,weight_decay=0.001)
    losses=[]
    for _ in range(epochs):
        opt.zero_grad();prediction=out(at@torch.relu(h(at@zt)))
        loss=((prediction[train]-yt[train])**2).mean();loss.backward();opt.step();losses.append(float(loss.detach()))
    with torch.no_grad():pred=out(at@torch.relu(h(at@zt))).numpy()
    ridge=Ridge(alpha=10).fit(z[train],y[train]);rp=ridge.predict(z[test])
    return {'graph_prediction':pred[test], 'ridge_prediction':rp, 'graph_all_prediction':pred,
            'training_steps':epochs, 'train_test_gene_overlap':0,'losses':losses,
            'state_dict':{'h':h.state_dict(),'out':out.state_dict()},'embedding_mean':mu,'embedding_std':sd}
