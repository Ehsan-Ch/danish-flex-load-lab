import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from threadpoolctl import threadpool_limits

REG = ('weekly','profile','ridge','boosted')
PROB = ('profile','logistic','boosted')
TREE = dict(max_iter=100,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=40,
            l2_regularization=1.,early_stopping=False,random_state=42)

class Models:
    def fit(self, X, y):
        with threadpool_limits(limits=2):
            self.reg = {
                'ridge':make_pipeline(StandardScaler(),Ridge(alpha=10)).fit(X,y),
                'boosted':HistGradientBoostingRegressor(loss='squared_error',**TREE).fit(X,y)}
            labels = (y<0).astype(int)
            self.constant = float(labels[0]) if len(np.unique(labels))<2 else None
            self.prob = {} if self.constant is not None else {
                'logistic':make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=1000,random_state=42)).fit(X,labels),
                'boosted':HistGradientBoostingClassifier(**TREE).fit(X,labels)}
        return self

    def raw(self, X):
        with threadpool_limits(limits=2):
            r = {k:m.predict(X) for k,m in self.reg.items()}
            p = {k:m.predict_proba(X)[:,1] for k,m in self.prob.items()} if self.constant is None else {k:np.full(len(X),self.constant) for k in ('logistic','boosted')}
        return r,p

    def calibrate(self, X, y, slots):
        _,p = self.raw(X)
        self.calibrators = {k:IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(v,y<0) for k,v in p.items()}
        self.profile = {}; self.frequency = {}
        for s in range(41):
            group = y[np.asarray(slots)==s]
            if not len(group):
                raise ValueError('Missing calibration start time')
            self.profile[s] = float(group.mean())
            self.frequency[s] = float(((group<0).sum()+1)/(len(group)+2))
        return self

    def predict(self, X, weekly, slots):
        r,p = self.raw(X)
        r.update(weekly=np.asarray(weekly),profile=np.array([self.profile[int(s)] for s in slots]))
        p = {k:self.calibrators[k].predict(v) for k,v in p.items()}
        p['profile'] = np.array([self.frequency[int(s)] for s in slots])
        return r,p

def probability_metrics(labels, probabilities):
    y,p = np.asarray(labels),np.asarray(probabilities,float)
    if y.ndim!=1 or y.shape!=p.shape or not len(y) or not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Invalid probabilities or labels')
    z = np.clip(p,1e-12,1-1e-12)
    both = len(np.unique(y))==2
    bins = []
    for i in range(10):
        take = (p>=i/10)&((p<(i+1)/10) if i<9 else (p<=1))
        n = int(take.sum())
        bins.append({'bin':i,'n':n,'predicted':float(p[take].mean()) if n else None,'observed':float(y[take].mean()) if n else None})
    return {'n':len(y),'events':int(y.sum()),'base_rate':float(y.mean()),
            'brier':float(((p-y)**2).mean()),'log_loss':float(-(y*np.log(z)+(1-y)*np.log(1-z)).mean()),
            'roc_auc':float(roc_auc_score(y,p)) if both else None,
            'average_precision':float(average_precision_score(y,p)) if both else None,'reliability':bins}
