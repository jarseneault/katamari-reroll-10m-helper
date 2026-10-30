import pefile, struct, sys, json, math
from unicorn import *
from unicorn.x86_const import *
P, MONO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
MISSION=int(sys.argv[4]); AREA=int(sys.argv[5]); STAGE=int(sys.argv[6])
idxs=[int(x) for x in sys.argv[7].split(',')]
pe=pefile.PE(P); BASE=pe.OPTIONAL_HEADER.ImageBase
img=pe.get_memory_mapped_image(ImageBase=BASE)
mu=Uc(UC_ARCH_X86, UC_MODE_64)
mu.mem_map(BASE,(len(img)+0xfff)&~0xfff); mu.mem_write(BASE,img)
STUB=0x10000000; mu.mem_map(STUB,0x10000); stubs={}; k=0
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        a=STUB+k*16; k+=1; mu.mem_write(a,b'\xc3'); mu.mem_write(imp.address,struct.pack('<Q',a))
        stubs[a]=(imp.name or b'?').decode()
STACK=0x20000000; mu.mem_map(STACK,0x200000)
GS=0x30000000; mu.mem_map(GS,0x10000)
mu.mem_write(GS+0x30,struct.pack('<Q',GS)); mu.mem_write(GS+0x58,struct.pack('<Q',GS+0x1000))
mu.mem_write(GS+0x1000,struct.pack('<Q',GS+0x2000)*64)
mu.reg_write(UC_X86_REG_GS_BASE,GS)
HEAP=0x50000000; HEAPSZ=0x8000000; mu.mem_map(HEAP,HEAPSZ); hp=[HEAP]
RET=0x40000000; mu.mem_map(RET,0x1000); mu.mem_write(RET,b'\xf4')
R=lambda r: mu.reg_read(r)
def xf(n): return struct.unpack('<f',struct.pack('<I',R(UC_X86_REG_XMM0+n) & 0xffffffff))[0] if False else struct.unpack('<f',(R(getattr(unicorn.x86_const,f'UC_X86_REG_XMM{n}'))&0xffffffff).to_bytes(4,'little'))[0]
import unicorn
def setxf(v): mu.reg_write(UC_X86_REG_XMM0, int.from_bytes(struct.pack('<f',v),'little'))
def setxd(v): mu.reg_write(UC_X86_REG_XMM0, int.from_bytes(struct.pack('<d',v),'little'))
def xd(): return struct.unpack('<d',(R(UC_X86_REG_XMM0)&0xffffffffffffffff).to_bytes(8,'little'))[0]
initterm=[]; seen={}
def hook(uc,addr,size,ud):
    n=stubs.get(addr)
    if n is None: return
    seen[n]=seen.get(n,0)+1
    rcx,rdx,r8=R(UC_X86_REG_RCX),R(UC_X86_REG_RDX),R(UC_X86_REG_R8)
    ret=0
    if n=='memset': uc.mem_write(rcx,bytes([rdx&0xff])*r8); ret=rcx
    elif n in('memcpy','memmove'): uc.mem_write(rcx,bytes(uc.mem_read(rdx,r8))) if r8 else None; ret=rcx
    elif n=='malloc': ret=hp[0]; hp[0]+=(rcx+15)&~15
    elif n=='strncmp':
        a=bytes(uc.mem_read(rcx,r8)); b=bytes(uc.mem_read(rdx,r8))
        a=a.split(b'\0')[0]; b=b.split(b'\0')[0]; ret=(a>b)-(a<b)
    elif n in ('_initterm','_initterm_e'): initterm.append((rcx,rdx))
    elif n=='sqrtf': setxf(math.sqrt(max(0,xf(0))))
    elif n=='sinf': setxf(math.sin(xf(0)))
    elif n=='cosf': setxf(math.cos(xf(0)))
    elif n=='acosf': setxf(math.acos(max(-1,min(1,xf(0)))))
    elif n=='atan2f': setxf(math.atan2(xf(0),xf(1)))
    elif n=='sqrt': setxd(math.sqrt(max(0,xd())))
    elif n=='acos': setxd(math.acos(max(-1,min(1,xd()))))
    elif n=='rand': ret=0
    elif n=='GetModuleHandleW': ret=BASE
    uc.reg_write(UC_X86_REG_RAX, ret & 0xffffffffffffffff)
mu.hook_add(UC_HOOK_CODE,hook,begin=STUB,end=STUB+0x10000)
def call(fn, ints=(), floats=None, stack=()):
    """floats: dict argpos->float for first 4; stack: list of 8-byte raw ints for args 5+"""
    sp=STACK+0x100000
    frame=struct.pack('<Q',RET)+b'\0'*0x20+b''.join(struct.pack('<Q',s & 0xffffffffffffffff) for s in stack)+b'\0'*0x40
    mu.mem_write(sp,frame); mu.reg_write(UC_X86_REG_RSP,sp)
    regs=[UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9]
    for i,v in enumerate(ints): mu.reg_write(regs[i], v & 0xffffffffffffffff)
    for i,v in (floats or {}).items(): mu.reg_write(getattr(unicorn.x86_const,f'UC_X86_REG_XMM{i}'), int.from_bytes(struct.pack('<f',v),'little'))
    mu.emu_start(fn,RET,count=200_000_000)
    return R(UC_X86_REG_RAX)
exp={e.name.decode():BASE+e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols}
# DllMain
call(BASE+pe.OPTIONAL_HEADER.AddressOfEntryPoint, ints=(BASE,1,0))
for a,b in initterm:
    for p in range(a,b,8):
        f=struct.unpack('<Q',mu.mem_read(p,8))[0]
        if f:
            try: call(f)
            except UcError as e: print("initterm fail",hex(f),e,hex(R(UC_X86_REG_RIP)))
data=open(MONO,'rb').read()
MD=0x60000000; mu.mem_map(MD,(len(data)+0xfff)&~0xfff); mu.mem_write(MD,data)
# MonoInitStart(ptr, mission, area, stage, kadai, clear, end)
call(exp['MonoInitStart'], ints=(MD,MISSION,AREA,STAGE), stack=(0,1,1))
call(exp['Init'], ints=(0,0,MISSION), floats={1:0.0})
f2i=lambda v: struct.unpack('<I',struct.pack('<f',v))[0]
res={}
for idx in idxs:
    try:
        # args: posX,posY,posZ,rotX in xmm0-3; then rotY,rotZ,rotW,sclX,sclY,sclZ (floats on stack), then 14 ints
        st=[f2i(0),f2i(0),f2i(0),f2i(1),f2i(1),f2i(1), idx,0,-1,-1,1,0,0,0,-1,0,-1,-1,-1,0]
        ci=call(exp['MonoInitAddProp'], floats={0:0.0,1:0.0,2:0.0,3:0.0}, stack=st)
        ci=struct.unpack('<i',struct.pack('<I',ci&0xffffffff))[0]
        if ci<0: res[idx]={'err':'addprop -1'}; continue
        out=STACK+0x1f0000
        call(exp['MonoGetVolume'], ints=(ci,out,out+8))
        vol=struct.unpack('<f',mu.mem_read(out,4))[0]; cd=struct.unpack('<f',mu.mem_read(out+8,4))[0]
        slot=0x18019b010+ci*0xbd0
        ext=struct.unpack('<3f',mu.mem_read(slot+0x938,12))
        res[idx]={'ci':ci,'volume':vol,'catchDiameterMM':cd,'ext':ext,'fac':struct.unpack('<2f',mu.mem_read(0x18008a888+idx*48,8))}
    except UcError as e:
        res[idx]={'err':str(e),'rip':hex(R(UC_X86_REG_RIP))}
json.dump(res,open(OUT,'w'),indent=0)
print('imports:',seen)
for k in list(res)[:8]: print(k,res[k])
