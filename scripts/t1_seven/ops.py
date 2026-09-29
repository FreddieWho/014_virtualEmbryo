import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp,logit
from scipy.spatial import cKDTree
from scipy import sparse
from scipy.sparse.linalg import cg


def bounded_weights(logw):
    v=np.asarray(logw,float);return np.exp(np.clip(v-np.median(v),-np.log(2),np.log(2)))


def moments(z):return np.column_stack([z,z*z])


def moment_fit(source,target,ridge,bound):
    f=np.asarray(source,float);target=np.asarray(target,float)
    def objective(theta):
        logits=f@theta;p=np.exp(logits-logsumexp(logits))
        return logsumexp(logits)-np.log(len(f))-target@theta+.5*ridge*(theta@theta),f.T@p-target+ridge*theta
    r=minimize(objective,np.zeros(f.shape[1]),jac=True,method='L-BFGS-B',bounds=[(-bound,bound)]*f.shape[1],options={'maxiter':2000,'ftol':1e-12,'gtol':1e-7})
    if not r.success:raise ValueError('moment optimizer failed: '+str(r.message))
    return r.x,{'success':bool(r.success),'iterations':int(r.nit),'objective':float(r.fun),'gradient_norm':float(np.linalg.norm(r.jac))}


def spd_power(c,power):
    values,vectors=np.linalg.eigh((c+c.T)*.5)
    if values.min()<=0:raise ValueError('nonpositive covariance')
    return (vectors*(values**power))@vectors.T


def gaussian_map(a,b):
    ah=spd_power(a,.5);ai=spd_power(a,-.5)
    return ai@spd_power(ah@b@ah,.5)@ai


def shrunk_cov(z,shrink):
    c=np.cov(z,rowvar=False);return (1-shrink)*c+shrink*np.eye(c.shape[0])*max(float(np.trace(c)/len(c)),1e-6)


def graph_fit(z,y,ids,k,alpha):
    n=len(z);tree=cKDTree(z);dist,nn=tree.query(z,k=min(k+1,n))
    # Tied coordinates need identity-based removal, not dropping the first hit.
    order=np.argsort(nn==np.arange(n)[:,None],axis=1,kind='stable')[:,:min(k,n-1)]
    dist=np.take_along_axis(dist,order,axis=1);nn=np.take_along_axis(nn,order,axis=1)
    scale=max(float(np.median(dist[dist>0])),1e-6) if np.any(dist>0) else 1.
    weights=np.exp(-np.minimum((dist/scale)**2,700))
    w=sparse.csr_matrix((weights.ravel(),(np.repeat(np.arange(n),nn.shape[1]),nn.ravel())),shape=(n,n));w=(w+w.T)*.5
    degree=np.asarray(w.sum(1)).ravel();inv=1/np.sqrt(np.maximum(degree,1e-12));sym=sparse.diags(inv)@w@sparse.diags(inv)
    # Solve the symmetric equivalent of (I-alpha D^-1 W) f=(1-alpha)y.
    rhs=(1-alpha)*np.sqrt(np.maximum(degree,1e-12))*y
    u,info=cg(sparse.eye(n,format='csr')-alpha*sym,rhs,rtol=1e-9,atol=1e-10,maxiter=2000)
    if info!=0:raise ValueError('graph solver failed '+str(info))
    f=u*inv;f[degree==0]=y[degree==0]
    residual=np.linalg.norm(f-alpha*(sparse.diags(1/np.maximum(degree,1e-12))@w)@f-(1-alpha)*y)
    if residual>1e-5:raise ValueError('graph linear residual')
    return {'z':z,'tree':tree,'values':np.clip(f,0,1),'ids':np.asarray(ids),'prior':float(y.mean()),'scale':scale,'solver_residual':float(residual)}


def graph_query(m,z,ids,k):
    kk=min(k+1,len(m['ids']));dist,nn=m['tree'].query(z,k=kk);dist=np.asarray(dist).reshape(len(z),kk);nn=np.asarray(nn).reshape(len(z),kk)
    valid=m['ids'][nn]!=np.asarray(ids)[:,None];valid&=np.cumsum(valid,axis=1)<=k
    weights=np.exp(-np.minimum((dist/m['scale'])**2,700))*valid
    den=weights.sum(1);p=np.divide((weights*m['values'][nn]).sum(1),den,out=np.full(len(z),m['prior']),where=den>1e-300)
    return logit(np.clip(p,1e-5,1-1e-5))-logit(np.clip(m['prior'],1e-5,1-1e-5))


def stability_weights(a,b,parts,required,unstable,seed):
    rng=np.random.default_rng(seed);aa=np.array_split(rng.permutation(len(a)),parts);bb=np.array_split(rng.permutation(len(b)),parts)
    def summaries(x):
        positive=x>0;counts=positive.sum(0);mean=np.divide(x.sum(0,dtype=float),counts,out=np.zeros(x.shape[1]),where=counts>0)
        return 1-positive.mean(0),mean
    pa,ma=summaries(a);pb,mb=summaries(b);steps0=[];steps1=[]
    for ia,ib in zip(aa,bb):
        p0,m0=summaries(a[ia]);p1,m1=summaries(b[ib]);steps0.append(p1-p0);steps1.append(m1-m0)
    w0=np.where(np.sum(np.sign(steps0)==np.sign(pb-pa),axis=0)>=required,1.,unstable)
    w1=np.where(np.sum(np.sign(steps1)==np.sign(mb-ma),axis=0)>=required,1.,unstable)
    return w0,w1,{'early_parts':aa,'late_parts':bb,'zero_changes':np.array(steps0),'positive_changes':np.array(steps1)}
