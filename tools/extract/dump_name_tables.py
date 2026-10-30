import UnityPy, sys, os
env = UnityPy.load(os.path.join(sys.argv[1],'katamari_Data','resources.assets'))
for o in env.objects:
    if o.type.name!='MonoBehaviour': continue
    try: n=o.peek_name()
    except Exception: continue
    if n in ('mononame','king_text'):
        raw=o.get_raw_data(); open(f"{sys.argv[2]}/{n}.bin","wb").write(raw); print(n,len(raw))
