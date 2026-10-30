import struct, json, sys
S=sys.argv[1]
class R:
    def __init__(s,b): s.b=b; s.p=0
    def i(s): v=struct.unpack_from('<i',s.b,s.p)[0]; s.p+=4; return v
    def f(s): v=struct.unpack_from('<f',s.b,s.p)[0]; s.p+=4; return v
    def al(s): s.p=(s.p+3)&~3
    def s(s_):
        n=s_.i(); v=s_.b[s_.p:s_.p+n].decode('utf-8'); s_.p+=n; s_.al(); return v
    def bool(s): v=s.b[s.p]!=0; s.p+=1; s.al(); return v
def header(r):
    r.p=12+8  # GameObject PPtr(12) + enabled(4 aligned) + Script PPtr(12) ... compute properly
r=R(open(f'{S}/mononame.bin','rb').read())
r.p=0; r.i(); r.i(); r.i()  # m_GameObject fileid,pathid(8)
r.p=12; r.bool(); r.i(); r.i(); r.i(); name=r.s(); assert name=='mononame', name
n=r.i(); out=[]
for k in range(n):
    e=dict(MONO_ID=r.s(),TEXT_ID1=r.s(),TEXT_ID2=r.s(),CATEGORY_ID=r.s(),SIZE=r.s(),SPOT_ID=r.s(),RARE=r.bool(),UNIT_ID=r.s())
    e['ANIM_NAME']=[r.s() for _ in range(r.i())]
    e['IGNORE_HOLE']=r.bool(); e['SIZE_ID']=r.s(); e['NICE_SETTING']=[r.f() for _ in range(r.i())]; e['ATTACH_PATCH']=r.bool()
    out.append(e)
assert r.p==len(r.b),(r.p,len(r.b))
json.dump(out,open(f'{S}/mononame.json','w'),ensure_ascii=False,indent=0)
r=R(open(f'{S}/king_text.bin','rb').read())
r.p=12; r.bool(); r.i(); r.i(); r.i(); assert r.s()=='king_text'
n=r.i(); kt={}
for k in range(n):
    tid=r.s(); r.s(); r.s(); kt[tid]=[r.s() for _ in range(r.i())]
assert r.p==len(r.b),(r.p,len(r.b))
json.dump(kt,open(f'{S}/king_text.json','w'),ensure_ascii=False)
print(len(out), len(kt)); 
for e in out[1:4]+out[-3:]: print(e['MONO_ID'],e['SIZE'],kt.get(e['TEXT_ID1']), kt.get(e['UNIT_ID']))
