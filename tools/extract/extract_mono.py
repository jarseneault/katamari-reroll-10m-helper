import UnityPy, sys, struct
env=UnityPy.load(sys.argv[1])
for o in env.objects:
    if o.type.name=='TextAsset' and o.peek_name()==sys.argv[2]:
        raw=o.get_raw_data()
        n=struct.unpack_from('<i',raw,0)[0]; p=(4+n+3)&~3
        ln=struct.unpack_from('<i',raw,p)[0]; b=raw[p+4:p+4+ln]
        open(sys.argv[3],'wb').write(b); print(len(b), b[:16].hex())
