"""WT-only dual-representation state atlas; no intervention identity features."""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans
from crossko_hurdle_v2 import CrossKOHurdle
from crossko import closed
class DetectionAtlas(CrossKOHurdle):
    def fit_atlas(self,wt,features=None):
        closed(wt)
        self.features=np.arange(wt.shape[1]) if features is None else np.asarray(features)
        self.G=wt.shape[1]
        self.pca=PCA(n_components=12,random_state=self.seed).fit(wt[:,self.features])
        self.detection_pca=PCA(n_components=12,random_state=self.seed).fit((wt[:,self.features]>0).astype('float32'))
        a=self.pca.transform(wt[:,self.features]);b=self.detection_pca.transform((wt[:,self.features]>0).astype('float32'))
        self.log_scale=float(np.sqrt(np.mean(a.var(0))));self.detection_scale=float(np.sqrt(np.mean(b.var(0))))
        z=np.c_[a/self.log_scale,b/self.detection_scale]
        self.km=MiniBatchKMeans(n_clusters=self.S,n_init=3,batch_size=1024,random_state=self.seed).fit(z)
        return self
    def assign(self,x):
        a=self.pca.transform(x[:,self.features]);b=self.detection_pca.transform((x[:,self.features]>0).astype('float32'))
        return self.km.predict(np.c_[a/self.log_scale,b/self.detection_scale])
