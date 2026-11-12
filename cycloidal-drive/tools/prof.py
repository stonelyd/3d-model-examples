import math
N=12; R=35.0; RR=3.25; E=1.2; CL=0.15
def profile(n_per_lobe=24):
    rr=RR+CL; pts=[]
    M=(N-1)*n_per_lobe
    for i in range(M):
        t=2*math.pi*i/M
        psi=math.atan2(math.sin((1-N)*t), R/(E*N)-math.cos((1-N)*t))
        x=R*math.cos(t)-rr*math.cos(t+psi)-E*math.cos(N*t)
        y=-R*math.sin(t)+rr*math.sin(t+psi)+E*math.sin(N*t)
        pts.append((x,y))
    return pts
def segdist(p,a,b):
    ax,ay=a;bx,by=b;px,py=p
    dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
    u=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(ax+u*dx-px, ay+u*dy-py)
def inside(p,poly):
    x,y=p;c=False;n=len(poly)
    for i in range(n):
        x1,y1=poly[i];x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y) and x < x1+(y-y1)*(x2-x1)/(y2-y1): c=not c
    return c
def check(pts, th_deg, ecc_sign=1, extra_rot=0.0):
    th=math.radians(th_deg)
    phi=-th/(N-1)+extra_rot
    cx,cy=ecc_sign*E*math.cos(th), ecc_sign*E*math.sin(th)
    c,s=math.cos(phi),math.sin(phi)
    W=[(cx+c*x-s*y, cy+s*x+c*y) for x,y in pts]
    res=[]
    for k in range(N):
        a=2*math.pi*k/N; p=(R*math.cos(a),R*math.sin(a))
        d=min(segdist(p,W[i],W[(i+1)%len(W)]) for i in range(len(W)))
        res.append((d-RR) * (-1 if inside(p,W) else 1))
    return min(res), max(res)
if __name__=="__main__":
    pts=profile()
    rs=[math.hypot(*p) for p in pts]; print("rmin rmax",min(rs),max(rs))
    for th in (0,37,132,200):
        print(th, check(pts,th), check(pts,th,-1,math.pi))
