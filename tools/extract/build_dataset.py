import json, re, math, struct, sys
S=sys.argv[1]; OUT=sys.argv[2]
props=json.load(open(f'{S}/placements.json'))
vols={int(k):v for k,v in json.load(open(f'{S}/volumes.json')).items()}
mn=json.load(open(f'{S}/mononame.json')); kt=json.load(open(f'{S}/king_text.json'))
src=open(f'{S}/src/MonoGroup.cs').read()
tbl=[int(x) for x in re.findall(r'-?\d+', src.split('{',2)[2])]
true={88:1009,41:1007,87:1008,89:1010,1055:1056,1057:1058,988:1011,190:1012,191:1013,192:1014,193:1015,1311:1312,141:519,524:497,525:498}
f32=lambda x: struct.unpack('<f',struct.pack('<f',x))[0]
# HUD: D_cm = 2*(100*cbrt(3V/4pi)+0.01); V for a displayed diameter (cm)
def V_at(dcm): r=(dcm/2-0.01)/100; return 4/3*math.pi*r**3
V10=V_at(1000.0)
eligible={}
for p in props:
    i=p['idx']
    reasons=[]
    if p['dispOff']>=0: reasons.append('dispOff')
    if p['reserve']: reasons.append('reserve')
    if 'DummyProps' in (p['go'] or ''): reasons.append('dummy')
    e=eligible.setdefault(i,{'placed':0,'ok':0,'reasons':set()})
    e['placed']+=1
    if not reasons: e['ok']+=1
    else: e['reasons'].update(reasons)
rows=[]
for i,e in sorted(eligible.items()):
    v=vols.get(i,{}).get('volume')
    why=[]
    if e['ok']==0: why.append('not-normally-placed:'+','.join(sorted(e['reasons'])))
    if tbl[i*6+3]==0: why.append('group-table')
    if 1476<=i<=1499 or 1695<=i<=1717: why.append('cousin')
    if v is None or v==1.0: why.append('no-model')
    t=true.get(i,i); m=mn[t]
    name=kt.get(m['TEXT_ID1'],['?','?'])
    rows.append(dict(idx=i, name=name[1].replace('\n',' ').strip() or name[0], nameJa=name[0].replace('\n',''), size=m['SIZE'],
        category=kt.get(m['CATEGORY_ID'],['',''])[1].replace('\n',' ') if m['CATEGORY_ID'] else '',
        volume=v, count=e['ok'], excluded=why))
ok=[r for r in rows if not r['excluded']]
print(len(rows), len(ok)); 
for r in rows:
    if r['excluded']: print('EXCL', r['idx'], r['name'], r['excluded'])
# gain: share of the object's volume added to the katamari on pickup (before the mission's size curve)
objs=[dict(id=r['idx'], name=r['name'], ja=r['nameJa'], size=r['size'], volume=r['volume'], placed=r['count'],
           gain=vols[r['idx']]['fac'][1], catchCm=vols[r['idx']]['catchDiameterMM']/10) for r in ok]
objs.sort(key=lambda o:(o['name'].lower(), o['volume']))
json.dump(dict(source='Katamari Damacy REROLL (Steam) - mission 21 "Make the North Star"', objects=objs), open(OUT,'w'), ensure_ascii=False, indent=1)
