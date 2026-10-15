exec(open('run2.py').read().split("cur=I.")[0])
a=pd.read_csv('assignment.csv').set_index('VD_Number')
sp=a.loc[split]; sp=sp[sp.status!='dropped']
sp['st']=[s.WARD[v] for v in sp.index]
print(sp.groupby('status').apply(lambda d:(d.ward_2026.astype(float)==d.st).sum()).to_dict(), sp.status.value_counts().to_dict())
print('dropped in split?', [v for v in a[a.status=='dropped'].index], [len(cw[v]) for v in a[a.status=='dropped'].index])
