import UnityPy, sys, os, json, collections
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
root=sys.argv[1]; bundle=sys.argv[2]
gen=TypeTreeGenerator("2018.1.9f2"); gen.load_local_game(root)
env=UnityPy.load(os.path.join(root,'katamari_Data/StreamingAssets/StandaloneWindows',bundle))
env.typetree_generator=gen
objs={o.path_id:o for o in env.objects}
out=[]
for o in env.objects:
    if o.type.name!='MonoBehaviour': continue
    try: tt=o.read_typetree()
    except Exception: continue
    if 'u16MonoNameIdx' not in tt: continue
    go=objs.get(tt['m_GameObject']['m_PathID'])
    name=go.read().m_Name if go else None
    out.append(dict(idx=tt['u16MonoNameIdx'], go=name, dispOff=tt['s8MonoDispOffAreaNo'], reserve=tt['isReserve'], unit=tt['u8UnitType']))
json.dump(out,open(sys.argv[3],'w'))
c=collections.Counter(x['go'] for x in out if 'Dummy' in (x['go'] or ''))
print(len(out), c.most_common(5), collections.Counter(x['dispOff'] for x in out), sum(x['reserve'] for x in out))
