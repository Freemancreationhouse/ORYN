"""ORYN Pattern Forge artwork import/generation.

This module is intentionally isolated from the proven motion/controller core.
It only turns artwork into normalized theta/rho coordinates and writes .thr text.
"""
from __future__ import annotations
from pathlib import Path
import math, re, xml.etree.ElementTree as ET
from typing import Iterable, List, Tuple

Point = Tuple[float, float]


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])


def _dedupe(points: Iterable[Point], eps: float = 1e-5) -> List[Point]:
    out=[]
    for p in points:
        p=(float(p[0]),float(p[1]))
        if not out or _dist(out[-1],p)>eps:
            out.append(p)
    return out


def _normalize(paths: List[List[Point]], fit: float = 0.94) -> List[List[Point]]:
    """
    Center artwork and scale it by its true radial extent so every point fits
    inside the circular sand table. This avoids the old square-bounds scaling
    that could clip diagonal corners after conversion.
    """
    pts=[p for path in paths for p in path]
    if not pts:
        raise ValueError("No usable geometry found")
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    cx=(min(xs)+max(xs))/2.0
    cy=(min(ys)+max(ys))/2.0
    centered=[(x-cx,y-cy) for x,y in pts]
    max_r=max((math.hypot(x,y) for x,y in centered),default=0.0)
    if max_r<1e-9:
        raise ValueError("Artwork geometry has no measurable size")
    target=max(0.1,min(float(fit),0.98))
    k=target/max_r
    return [[((x-cx)*k,(y-cy)*k) for x,y in path] for path in paths]


def _nearest_order(paths: List[List[Point]]) -> List[List[Point]]:
    pending=[p[:] for p in paths if len(p)>1]
    if not pending: return []
    ordered=[pending.pop(0)]
    while pending:
        end=ordered[-1][-1]
        best=None
        for i,p in enumerate(pending):
            d0=_dist(end,p[0]); d1=_dist(end,p[-1])
            cand=(min(d0,d1),i,d1<d0)
            if best is None or cand<best: best=cand
        _,i,rev=best
        p=pending.pop(i)
        if rev: p.reverse()
        ordered.append(p)
    return ordered


def _resample_line(a: Point,b: Point,step=.02):
    d=_dist(a,b); n=max(1,int(math.ceil(d/step)))
    return [(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]


def _polar(p: Point) -> Tuple[float,float]:
    return math.atan2(p[1],p[0]), math.hypot(p[0],p[1])


def _arc_connector(a: Point, b: Point, lane_radius: float=.985, step: float=.012) -> List[Point]:
    """
    Route a long unavoidable travel move around the quiet outer lane instead
    of cutting a straight line through the artwork.

    Pattern artwork is normally fitted to <= .94 radius, leaving the .985
    perimeter lane available for disconnected-island travel.
    """
    lane=max(.955,min(.997,float(lane_radius)))
    ta,ra=_polar(a); tb,rb=_polar(b)

    # unwrap the shortest boundary arc
    while tb-ta>math.pi: tb-=2*math.pi
    while tb-ta<-math.pi: tb+=2*math.pi

    out=[]
    # radial outward from a to lane
    n=max(1,int(math.ceil(abs(lane-ra)/step)))
    for i in range(n+1):
        r=ra+(lane-ra)*i/n
        out.append((math.cos(ta)*r,math.sin(ta)*r))

    # boundary arc
    arc_len=abs(tb-ta)*lane
    n=max(1,int(math.ceil(arc_len/step)))
    for i in range(1,n+1):
        t=ta+(tb-ta)*i/n
        out.append((math.cos(t)*lane,math.sin(t)*lane))

    # radial inward from lane to b
    n=max(1,int(math.ceil(abs(lane-rb)/step)))
    for i in range(1,n+1):
        r=lane+(rb-lane)*i/n
        out.append((math.cos(tb)*r,math.sin(tb)*r))

    if out:
        out[-1]=b
    return _dedupe(out)


def _route_order(paths: List[List[Point]], start_mode: str="auto") -> List[List[Point]]:
    """
    Endpoint-aware route ordering.

    Tests several plausible first islands, then greedily selects the nearest
    next endpoint while freely reversing open paths. This gives materially
    shorter travel than a fixed source-file ordering without changing artwork.
    """
    paths=[p[:] for p in paths if len(p)>1]
    if len(paths)<2:
        return paths

    mode=(start_mode or "auto").lower()

    def center_score(p):
        return min(math.hypot(*p[0]),math.hypot(*p[-1]))

    def perimeter_score(p):
        return -max(math.hypot(*p[0]),math.hypot(*p[-1]))

    indices=list(range(len(paths)))
    if mode=="center":
        seeds=sorted(indices,key=lambda i:center_score(paths[i]))[:min(6,len(paths))]
    elif mode=="perimeter":
        seeds=sorted(indices,key=lambda i:perimeter_score(paths[i]))[:min(6,len(paths))]
    else:
        seeds=set()
        seeds.update(sorted(indices,key=lambda i:center_score(paths[i]))[:3])
        seeds.update(sorted(indices,key=lambda i:perimeter_score(paths[i]))[:3])
        # Also include longest paths because starting on dominant artwork often
        # reduces tiny-island connector churn.
        seeds.update(sorted(indices,key=lambda i:-len(paths[i]))[:3])
        seeds=list(seeds)

    best_order=None
    best_cost=None
    for seed in seeds:
        pending=[p[:] for i,p in enumerate(paths) if i!=seed]
        first=paths[seed][:]
        # choose orientation based on requested start preference
        if mode=="center" and math.hypot(*first[-1])<math.hypot(*first[0]):
            first.reverse()
        elif mode=="perimeter" and math.hypot(*first[-1])>math.hypot(*first[0]):
            first.reverse()
        ordered=[first]
        cost=0.0
        while pending:
            end=ordered[-1][-1]
            best=None
            for i,q in enumerate(pending):
                d0=_dist(end,q[0]); d1=_dist(end,q[-1])
                cand=(min(d0,d1),i,d1<d0)
                if best is None or cand<best:
                    best=cand
            d,i,rev=best
            q=pending.pop(i)
            if rev:q.reverse()
            cost+=d
            ordered.append(q)
        if best_cost is None or cost<best_cost:
            best_cost=cost
            best_order=ordered
    return best_order or paths


def _join_clean(paths: List[List[Point]], max_bridge: float=.065,
                start_mode: str="auto", preserve_all: bool=True,
                lane_radius: float=.985) -> Tuple[List[Point],dict]:
    """
    Produce one physically executable continuous XY route.

    Short gaps use a direct connector. Longer unavoidable gaps are routed
    around a reserved perimeter travel lane instead of crossing through the
    design. If preserve_all=False they are skipped (legacy behavior).
    """
    ordered=_route_order(paths,start_mode)
    if not ordered:
        return [],{"skipped_islands":0,"direct_connectors":0,"perimeter_connectors":0,
                   "connector_distance":0.0}

    route=list(ordered[0])
    skipped=0; direct=0; perimeter=0; connector_distance=0.0
    for path in ordered[1:]:
        if not path: continue
        gap=_dist(route[-1],path[0])
        connector_distance+=gap
        if gap<=max_bridge:
            bridge=_resample_line(route[-1],path[0],.010)
            route.extend(bridge[1:])
            direct+=1
        elif preserve_all:
            bridge=_arc_connector(route[-1],path[0],lane_radius=lane_radius,step=.010)
            route.extend(bridge[1:])
            perimeter+=1
        else:
            skipped+=1
            continue
        route.extend(path[1:])

    return _dedupe(route),{
        "skipped_islands":skipped,
        "direct_connectors":direct,
        "perimeter_connectors":perimeter,
        "connector_distance":round(connector_distance,4),
    }


def _resample_polyline(points: List[Point], max_step: float=.012) -> List[Point]:
    """Bound XY step length for smoother real-machine motion."""
    if len(points)<2:return points[:]
    step=max(.003,min(.035,float(max_step)))
    out=[points[0]]
    for a,b in zip(points,points[1:]):
        d=_dist(a,b)
        n=max(1,int(math.ceil(d/step)))
        for i in range(1,n+1):
            out.append((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n))
    return _dedupe(out,1e-7)


def _xy_to_thr(points: List[Point]) -> List[Tuple[float,float]]:
    """
    Convert normalized XY to machine THR while avoiding meaningless theta
    whipping at the exact center.
    """
    if len(points)<2:
        raise ValueError("Generated route is too short")
    out=[]
    last_theta=0.0
    center_freeze=.012
    for x,y in points:
        rho=min(1.0,max(0.0,math.hypot(x,y)))
        if rho<center_freeze:
            theta=last_theta
        else:
            theta=math.atan2(y,x)
            while theta-last_theta>math.pi: theta-=2*math.pi
            while theta-last_theta<-math.pi: theta+=2*math.pi
        if not (math.isfinite(theta) and math.isfinite(rho)):
            raise ValueError("Generated route contains a non-finite coordinate")
        out.append((theta,rho))
        last_theta=theta
    return out



def _densify_thr(points: List[Tuple[float,float]], max_theta_step: float=0.11, max_rho_step: float=0.012) -> List[Tuple[float,float]]:
    """Bound polar step size so generated artwork cannot cause a sharp motor jerk.

    This is especially important when a Cartesian stroke passes very close to
    table centre, where theta can change rapidly while rho is tiny.  The
    interpolated THR points are also what the preview displays and what gets
    saved, preserving preview == machine route.
    """
    if len(points)<2:
        return points[:]
    mt=max(0.03,min(0.30,float(max_theta_step)))
    mr=max(0.004,min(0.03,float(max_rho_step)))
    out=[points[0]]
    for (t0,r0),(t1,r1) in zip(points,points[1:]):
        dt=t1-t0; dr=r1-r0
        n=max(1,int(math.ceil(abs(dt)/mt)),int(math.ceil(abs(dr)/mr)))
        for i in range(1,n+1):
            f=i/n
            out.append((t0+dt*f,r0+dr*f))
    return out

def _validate_thr(points: List[Tuple[float,float]]) -> dict:
    if len(points)<2:
        raise ValueError("Generated THR route is too short")
    max_dt=0.0; max_dr=0.0
    for i,(t,r) in enumerate(points):
        if not (math.isfinite(t) and math.isfinite(r)):
            raise ValueError(f"Invalid THR coordinate at point {i}")
        if r < -1e-9 or r > 1.000001:
            raise ValueError(f"Rho outside table boundary at point {i}: {r}")
        if i:
            max_dt=max(max_dt,abs(t-points[i-1][0]))
            max_dr=max(max_dr,abs(r-points[i-1][1]))
    return {
        "max_theta_step":round(max_dt,5),
        "max_rho_step":round(max_dr,5),
        "validated":1,
    }


def _svg_paths(path: Path) -> List[List[Point]]:
    try:
        from svgpathtools import svg2paths2
    except Exception as e:
        raise RuntimeError("SVG import requires svgpathtools") from e
    segs, attrs, svgattrs = svg2paths2(str(path))
    paths=[]
    for seg in segs:
        length=max(float(seg.length(error=1e-3)),1.0)
        n=max(12,min(2500,int(length/2.0)))
        pts=[]
        for i in range(n+1):
            z=seg.point(i/n); pts.append((z.real,-z.imag))
        pts=_dedupe(pts)
        if len(pts)>2: paths.append(pts)
    return paths


def _dxf_paths(path: Path) -> List[List[Point]]:
    try:
        import ezdxf
    except Exception as e:
        raise RuntimeError("DXF import requires ezdxf") from e
    doc=ezdxf.readfile(str(path)); msp=doc.modelspace(); paths=[]
    for e in msp:
        typ=e.dxftype()
        try:
            if typ=="LINE":
                paths.append([(e.dxf.start.x,-e.dxf.start.y),(e.dxf.end.x,-e.dxf.end.y)])
            elif typ in ("LWPOLYLINE","POLYLINE"):
                pts=[]
                if typ=="LWPOLYLINE": pts=[(p[0],-p[1]) for p in e.get_points("xy")]
                else: pts=[(v.dxf.location.x,-v.dxf.location.y) for v in e.vertices]
                if getattr(e,"closed",False) and pts: pts.append(pts[0])
                if len(pts)>1: paths.append(pts)
            elif typ in ("CIRCLE","ARC"):
                c=e.dxf.center; r=float(e.dxf.radius)
                a0=0.0 if typ=="CIRCLE" else math.radians(float(e.dxf.start_angle))
                a1=2*math.pi if typ=="CIRCLE" else math.radians(float(e.dxf.end_angle))
                if a1<=a0: a1+=2*math.pi
                n=max(48,int(abs(a1-a0)*r/2))
                paths.append([(c.x+r*math.cos(a0+(a1-a0)*i/n),-(c.y+r*math.sin(a0+(a1-a0)*i/n))) for i in range(n+1)])
            elif typ in ("SPLINE","ELLIPSE"):
                pts=[(p.x,-p.y) for p in e.flattening(0.5)]
                if len(pts)>1: paths.append(pts)
        except Exception:
            continue
    return paths


def _components(mask):
    import numpy as np
    h,w=mask.shape; seen=np.zeros_like(mask,dtype=bool); comps=[]
    for y in range(h):
        for x in range(w):
            if not mask[y,x] or seen[y,x]: continue
            stack=[(y,x)]; seen[y,x]=1; c=[]
            while stack:
                yy,xx=stack.pop(); c.append((yy,xx))
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        if not(dx or dy): continue
                        ny,nx=yy+dy,xx+dx
                        if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                            seen[ny,nx]=1; stack.append((ny,nx))
            comps.append(c)
    return comps


def _zhang_suen(mask):
    import numpy as np
    im=mask.astype(np.uint8).copy(); h,w=im.shape; changed=True
    while changed:
        changed=False
        for phase in (0,1):
            rem=[]
            for y in range(1,h-1):
                for x in range(1,w-1):
                    if im[y,x]!=1: continue
                    p2,p3,p4,p5,p6,p7,p8,p9=im[y-1,x],im[y-1,x+1],im[y,x+1],im[y+1,x+1],im[y+1,x],im[y+1,x-1],im[y,x-1],im[y-1,x-1]
                    ns=[p2,p3,p4,p5,p6,p7,p8,p9]; n=sum(ns)
                    if n<2 or n>6: continue
                    trans=sum(1 for a,b in zip(ns,ns[1:]+ns[:1]) if a==0 and b==1)
                    if trans!=1: continue
                    if phase==0 and (p2*p4*p6 or p4*p6*p8): continue
                    if phase==1 and (p2*p4*p8 or p2*p6*p8): continue
                    rem.append((y,x))
            if rem:
                changed=True
                for p in rem: im[p]=0
    return im.astype(bool)


def _skeleton_adjacency(pixels):
    """Build a clean pixel graph from a thinned skeleton.

    Diagonal neighbours are kept for real diagonal strokes but the redundant
    diagonal of an ordinary 90-degree corner is suppressed.  This prevents
    tiny triangular loops that make the sand ball chatter at corners.
    """
    pixels=set(pixels)
    adj={}
    for y,x in pixels:
        ns=[]
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if not (dx or dy):
                    continue
                q=(y+dy,x+dx)
                if q not in pixels:
                    continue
                if dx and dy and ((y,x+dx) in pixels or (y+dy,x) in pixels):
                    continue
                ns.append(q)
        adj[(y,x)]=ns
    return adj


def _prune_short_spurs(pixels, max_len=4, passes=3):
    """Remove only tiny skeleton whiskers caused by JPEG/photo noise."""
    pixels=set(pixels)
    removed=0
    for _ in range(max(1,int(passes))):
        adj=_skeleton_adjacency(pixels)
        kill=set()
        endpoints=[v for v,n in adj.items() if len(n)==1]
        for start in endpoints:
            if start in kill or start not in adj:
                continue
            trail=[start]
            prev=None
            cur=start
            for _step in range(max_len+1):
                nbs=[n for n in adj.get(cur,()) if n!=prev]
                if not nbs:
                    break
                nxt=nbs[0]
                trail.append(nxt)
                prev,cur=cur,nxt
                deg=len(adj.get(cur,()))
                if deg!=2:
                    # A tiny dead branch ending at a junction is photographic
                    # noise.  Keep the junction itself.
                    if deg>=3 and len(trail)-1<=max_len:
                        kill.update(trail[:-1])
                    break
                if len(trail)-1>max_len:
                    break
        if not kill:
            break
        pixels.difference_update(kill)
        removed += len(kill)
    return pixels,removed


def _bfs_path(adj, start, targets):
    """Shortest existing skeleton path from start to any target."""
    from collections import deque
    q=deque([start]); prev={start:None}
    target_set=set(targets)
    found=None
    while q:
        v=q.popleft()
        if v!=start and v in target_set:
            found=v; break
        for n in adj.get(v,()):
            if n not in prev:
                prev[n]=v; q.append(n)
    if found is None:
        return None
    out=[]; cur=found
    while cur is not None:
        out.append(cur); cur=prev[cur]
    out.reverse()
    return out


def _walk_component(comp, shape):
    """Create a continuous, low-retrace route through one skeleton component.

    The old Pattern Forge used a DFS walk that returned to every branch point,
    which duplicated large parts of a drawing and produced visibly messy,
    jerky paths.  This version treats the skeleton as an undirected graph,
    eulerises only the unavoidable odd vertices by duplicating *existing ink
    strokes*, and then emits one Euler trail.  A one-stroke free-hand drawing
    is therefore followed once, in its natural geometry.
    """
    pixels,spur_removed=_prune_short_spurs(comp,max_len=4,passes=3)
    adj=_skeleton_adjacency(pixels)
    # Drop graph-isolated residue.
    adj={v:[n for n in ns if n in adj] for v,ns in adj.items() if ns}
    if not adj:
        return []

    def edge(a,b):
        return (a,b) if a<=b else (b,a)

    base_edges=set()
    for a,ns in adj.items():
        for b in ns:
            base_edges.add(edge(a,b))
    if not base_edges:
        return []

    # Edge multiplicity starts at one.  Pair odd graph vertices using shortest
    # paths along the artwork itself; those are the only segments that may be
    # retraced, and only when topology makes a single continuous route
    # impossible otherwise.
    counts={e:1 for e in base_edges}
    odd=[v for v,ns in adj.items() if len(ns)%2==1]
    original_odd=len(odd)
    pending=set(odd)
    duplicated=0
    while len(pending)>2:
        a=min(pending)
        pending.remove(a)
        path=_bfs_path(adj,a,pending)
        if not path:
            break
        b=path[-1]
        pending.discard(b)
        for u,v in zip(path,path[1:]):
            e=edge(u,v); counts[e]=counts.get(e,0)+1; duplicated+=1

    # Build mutable multigraph.
    multi={v:{} for v in adj}
    for (a,b),c in counts.items():
        multi.setdefault(a,{})[b]=multi.setdefault(a,{}).get(b,0)+c
        multi.setdefault(b,{})[a]=multi.setdefault(b,{}).get(a,0)+c

    remaining_odd=[v for v,ns in multi.items() if sum(ns.values())%2==1]
    if remaining_odd:
        start=min(remaining_odd)
    else:
        # Prefer an endpoint nearest the component's lower-left source order;
        # deterministic output is important for repeatable previews.
        start=min(multi)

    stack=[start]; circuit=[]
    while stack:
        v=stack[-1]
        candidates=[n for n,c in multi.get(v,{}).items() if c>0]
        if candidates:
            # Prefer straight continuation.  This reduces jitter at crossings
            # while Hierholzer still guarantees every multigraph edge is used.
            if len(stack)>=2:
                py,px=stack[-2]; vy,vx=v
                iv=(vx-px,vy-py)
                il=(iv[0]*iv[0]+iv[1]*iv[1])**0.5 or 1.0
                def turn_score(n):
                    ny,nx=n; ov=(nx-vx,ny-vy)
                    ol=(ov[0]*ov[0]+ov[1]*ov[1])**0.5 or 1.0
                    return -(iv[0]*ov[0]+iv[1]*ov[1])/(il*ol), n
                n=min(candidates,key=turn_score)
            else:
                n=min(candidates)
            multi[v][n]-=1; multi[n][v]-=1
            stack.append(n)
        else:
            circuit.append(stack.pop())

    route=list(reversed(circuit))
    _walk_component.last_stats={
        "skeleton_edges":len(base_edges),
        "odd_vertices":original_odd,
        "retrace_edges":duplicated,
        "spur_pixels_removed":spur_removed,
        "retrace_ratio":round(duplicated/max(1,len(base_edges)),4),
    }
    return [(float(x),float(y)) for y,x in route]



def _binary_erode(mask):
    """3x3 binary erosion using NumPy only."""
    import numpy as np
    h,w=mask.shape
    if h<3 or w<3:
        return mask.copy()
    out=np.ones_like(mask,dtype=bool)
    padded=np.pad(mask,1,mode="constant",constant_values=False)
    for dy in range(3):
        for dx in range(3):
            out &= padded[dy:dy+h,dx:dx+w]
    return out


def _binary_dilate(mask):
    """3x3 binary dilation using NumPy only."""
    import numpy as np
    h,w=mask.shape
    out=np.zeros_like(mask,dtype=bool)
    padded=np.pad(mask,1,mode="constant",constant_values=False)
    for dy in range(3):
        for dx in range(3):
            out |= padded[dy:dy+h,dx:dx+w]
    return out


def _remove_small_components(mask, min_pixels):
    import numpy as np
    clean=np.zeros_like(mask,dtype=bool)
    comps=_components(mask)
    if not comps:
        return clean,[]
    comps.sort(key=len,reverse=True)
    kept=[]
    for comp in comps:
        if len(comp)>=min_pixels:
            kept.append(comp)
            for p in comp:
                clean[p]=1
    return clean,kept


def _component_bbox(comp):
    ys=[p[0] for p in comp]; xs=[p[1] for p in comp]
    return min(xs),min(ys),max(xs),max(ys)


def _bridge_short_gaps(mask, max_gap_px=8):
    """
    Join only genuinely small breaks between major line fragments.
    This repairs broken JPEG/PNG antialiasing without creating long
    pass-lines across the artwork.
    """
    import numpy as np, math
    comps=[c for c in _components(mask) if len(c)>=8]
    if len(comps)<2:
        return mask,0
    comps.sort(key=len,reverse=True)
    joined=0
    # Work from large to small; bounded pair search.
    for _ in range(min(12,len(comps)-1)):
        comps=[c for c in _components(mask) if len(c)>=8]
        comps.sort(key=len,reverse=True)
        best=None
        for i in range(min(len(comps),18)):
            a=comps[i]
            aa=a[::max(1,len(a)//180)]
            for j in range(i+1,min(len(comps),18)):
                b=comps[j]
                bb=b[::max(1,len(b)//180)]
                for pa in aa:
                    for pb in bb:
                        d2=(pa[0]-pb[0])**2+(pa[1]-pb[1])**2
                        if best is None or d2<best[0]:
                            best=(d2,pa,pb)
        if best is None or math.sqrt(best[0])>max_gap_px:
            break
        _,a,b=best
        y0,x0=a; y1,x1=b
        dx=abs(x1-x0); sx=1 if x0<x1 else -1
        dy=-abs(y1-y0); sy=1 if y0<y1 else -1
        err=dx+dy
        while True:
            mask[y0,x0]=1
            if x0==x1 and y0==y1: break
            e2=2*err
            if e2>=dy: err+=dy; x0+=sx
            if e2<=dx: err+=dx; y0+=sy
        joined+=1
    return mask,joined


def _auto_crop_gray(im):
    """
    Crop broad blank margins without cutting artwork.
    Helps web-downloaded images where the actual line art occupies only
    the central portion of a large white/black canvas.
    """
    import numpy as np
    arr=np.asarray(im,dtype=np.uint8)
    if arr.size==0:
        return im
    # Difference from median border tone.
    border=np.concatenate([arr[0,:],arr[-1,:],arr[:,0],arr[:,-1]])
    bg=float(np.median(border))
    delta=np.abs(arr.astype(float)-bg)
    ys,xs=np.where(delta>14)
    if len(xs)<20:
        return im
    pad=8
    x0=max(0,int(xs.min())-pad); x1=min(arr.shape[1],int(xs.max())+pad+1)
    y0=max(0,int(ys.min())-pad); y1=min(arr.shape[0],int(ys.max())+pad+1)
    if x1-x0<20 or y1-y0<20:
        return im
    return im.crop((x0,y0,x1,y1))


def _otsu_threshold(arr):
    """Small NumPy-only Otsu implementation (no OpenCV dependency on Pi)."""
    import numpy as np
    a=np.asarray(arr,dtype=np.uint8)
    hist=np.bincount(a.ravel(),minlength=256).astype(float)
    total=a.size
    if total<=0:
        return 128
    sum_total=float(np.dot(np.arange(256),hist))
    sum_b=0.0; w_b=0.0; best=-1.0; threshold=128
    for t in range(256):
        w_b += hist[t]
        if w_b<=0: continue
        w_f=total-w_b
        if w_f<=0: break
        sum_b += t*hist[t]
        m_b=sum_b/w_b; m_f=(sum_total-sum_b)/w_f
        between=w_b*w_f*(m_b-m_f)*(m_b-m_f)
        if between>best:
            best=between; threshold=t
    return int(threshold)


def _mask_quality(mask):
    """Score a candidate line mask for photographed/sketched artwork."""
    import numpy as np
    cov=float(mask.mean())
    if cov<0.0008 or cov>0.42:
        return -1e9
    comps=_components(mask)
    if not comps:
        return -1e9
    sizes=sorted((len(c) for c in comps),reverse=True)
    ink=max(1,int(mask.sum()))
    largest=sizes[0]/ink
    # Thin drawings commonly occupy 0.5–15% of a page.  Reward coherent ink
    # without forcing a single component (letters/facial details may separate).
    coverage_score=1.0-min(1.0,abs(cov-0.045)/0.18)
    coherent=min(1.0,sum(sizes[:12])/ink)
    clutter=min(1.0,len(sizes)/180.0)
    return coverage_score*1.8 + largest*0.9 + coherent*0.8 - clutter*0.45


def _prepare_raster_mask(path: Path, threshold=128, invert=False):
    """Photo-aware free-hand line extraction.

    Handles phone photographs of pencil/pen drawings under uneven lighting by
    comparing every pixel with a locally blurred paper/background estimate.
    It also evaluates the classic global threshold and automatically chooses
    whichever candidate looks most like coherent line artwork.
    """
    import numpy as np
    from PIL import Image, ImageOps, ImageFilter

    im=Image.open(path)
    im=ImageOps.exif_transpose(im).convert("L")
    im=_auto_crop_gray(im)
    im.thumbnail((720,720),Image.Resampling.LANCZOS)
    im=ImageOps.autocontrast(im,cutoff=0.5)
    arr=np.asarray(im,dtype=np.uint8)

    # Global candidate preserves already-clean scans/screenshots.
    manual=max(20,min(240,int(threshold)))
    raw = arr>manual if invert else arr<manual

    # Local-background candidate removes page shadows and gentle gradients.
    radius=max(7.0,min(im.size)/28.0)
    bg=np.asarray(im.filter(ImageFilter.GaussianBlur(radius=radius)),dtype=np.float32)
    a=arr.astype(np.float32)
    signal=(a-bg) if invert else (bg-a)
    ink=np.clip(signal,0,255).astype(np.uint8)
    ot=_otsu_threshold(ink)
    # Slider remains useful: higher threshold = more sensitive / more ink.
    sensitivity=1.38-(manual/255.0)*0.78
    local_cut=max(3,int(max(ot,6)*sensitivity))
    adaptive=ink>=local_cut

    # A third candidate catches faint pencil strokes where local Otsu can be a
    # little conservative.  Percentile is computed only from positive detail.
    pos=ink[ink>2]
    if pos.size:
        q=max(4,int(np.percentile(pos,58)))
        faint=ink>=max(3,min(local_cut,q))
    else:
        faint=adaptive

    candidates=[("photo-adaptive",adaptive),("photo-faint",faint),("global",raw)]
    mode,mask=max(candidates,key=lambda item:_mask_quality(item[1]))
    coverage=float(mask.mean())

    # Filled artwork/logos should become their outline, not a dense scribble.
    if coverage>0.26:
        er=_binary_erode(mask)
        mask=mask & ~er
        mode += "-outline"

    # Suppress image-frame artefacts and gently repair one-pixel breaks.
    if mask.shape[0]>6 and mask.shape[1]>6:
        mask[:3,:]=0; mask[-3:,:]=0; mask[:,:3]=0; mask[:,-3:]=0
    mask=_binary_dilate(mask)
    mask=_binary_erode(mask)

    _prepare_raster_mask.last_stats={
        "trace_mode":mode,
        "source_coverage":round(coverage,4),
        "local_threshold":local_cut,
        "otsu_detail":ot,
        "photo_cleanup":1,
    }
    return mask,mode,coverage


def _raster_paths(path: Path, threshold=128, invert=False) -> List[List[Point]]:
    """Turn a photographed/free-hand drawing into clean continuous strokes."""
    import numpy as np

    mask,trace_mode,coverage=_prepare_raster_mask(path,threshold,invert)
    comps=_components(mask)
    if not comps:
        raise ValueError("No artwork lines detected. Try Invert or adjust Image threshold.")
    comps.sort(key=len,reverse=True)
    largest=len(comps[0])

    # Remove specks/dust but retain small intentional details.
    min_pixels=max(6,min(28,int(largest*.0035)))
    clean,kept=_remove_small_components(mask,min_pixels)
    if not kept:
        raise ValueError("No clean line geometry detected. Try Invert or adjust Image threshold.")

    clean,joined=_bridge_short_gaps(clean,max_gap_px=6)
    skel=_zhang_suen(clean)
    comps=[c for c in _components(skel) if len(c)>=5]
    comps.sort(key=len,reverse=True)
    if not comps:
        raise ValueError("Artwork could not be converted into a clean centerline.")

    largest=len(comps[0])
    min_keep=max(5,int(largest*.0025))
    selected=[c for c in comps if len(c)>=min_keep][:256]

    paths=[]; retrace_edges=0; skeleton_edges=0; spurs=0; odd_vertices=0
    for comp in selected:
        route=_walk_component(comp,skel.shape)
        st=getattr(_walk_component,"last_stats",{}) or {}
        retrace_edges+=int(st.get("retrace_edges",0))
        skeleton_edges+=int(st.get("skeleton_edges",0))
        spurs+=int(st.get("spur_pixels_removed",0))
        odd_vertices+=int(st.get("odd_vertices",0))
        if len(route)>=4:
            paths.append(route)

    if not paths:
        raise ValueError("Generated route is empty.")

    prep=getattr(_prepare_raster_mask,"last_stats",{}) or {}
    _raster_paths.last_stats={
        **prep,
        "trace_mode":trace_mode,
        "source_coverage":round(coverage,4),
        "components_detected":len(comps),
        "components_retained":len(paths),
        "small_gaps_repaired":joined,
        "skeleton_edges":skeleton_edges,
        "retrace_edges":retrace_edges,
        "retrace_ratio":round(retrace_edges/max(1,skeleton_edges),4),
        "odd_vertices":odd_vertices,
        "spur_pixels_removed":spurs,
    }
    return paths



def _gcode_paths(path: Path) -> List[List[Point]]:
    """Extract drawable XY geometry from common G-code.

    Supports modal G0/G1/G2/G3, G90/G91, G20/G21, I/J arcs and common R
    arcs.  G0 is treated as a non-drawing reposition (new island).  Z and
    other machine-only axes are ignored because a sand-table ball cannot lift.
    """
    text=path.read_text(encoding="utf-8",errors="ignore")
    absolute=True; unit=1.0; motion_mode=0
    x=y=0.0; have_pos=False
    current=[]; paths=[]

    def flush():
        nonlocal current
        q=_dedupe(current,1e-9)
        if len(q)>1: paths.append(q)
        current=[]

    def words(line):
        line=re.sub(r'\([^)]*\)',' ',line)
        line=line.split(';',1)[0].upper()
        out=[]
        for m in re.finditer(r'([A-Z])\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)',line):
            try: out.append((m.group(1),float(m.group(2))))
            except ValueError: pass
        return out

    def arc_center_from_r(start,end,radius,clockwise):
        x0,y0=start; x1,y1=end
        dx=x1-x0; dy=y1-y0; chord=math.hypot(dx,dy)
        R=abs(radius)
        if chord<1e-12 or R<chord/2:
            return None
        mx=(x0+x1)/2; my=(y0+y1)/2
        h=math.sqrt(max(0.0,R*R-(chord/2)**2))
        ux=-dy/chord; uy=dx/chord
        candidates=[(mx+ux*h,my+uy*h),(mx-ux*h,my-uy*h)]
        def sweep_for(c):
            cx,cy=c; a0=math.atan2(y0-cy,x0-cx); a1=math.atan2(y1-cy,x1-cx)
            if clockwise:
                while a1>=a0: a1-=2*math.pi
            else:
                while a1<=a0: a1+=2*math.pi
            return a1-a0
        scored=[(abs(sweep_for(c)),c,sweep_for(c)) for c in candidates]
        # Positive R normally requests the minor arc; negative R the major.
        if radius>=0:
            _,c,sw=min(scored,key=lambda z:z[0])
        else:
            _,c,sw=max(scored,key=lambda z:z[0])
        return c,sw

    for raw in text.splitlines():
        ws=words(raw)
        if not ws: continue
        gs=[int(round(v)) for k,v in ws if k=='G']
        if 20 in gs: unit=25.4
        if 21 in gs: unit=1.0
        if 90 in gs: absolute=True
        if 91 in gs: absolute=False
        explicit=next((g for g in gs if g in (0,1,2,3)),None)
        if explicit is not None:
            motion_mode=explicit
        # Coordinate-only lines inherit the current modal motion.
        if not any(k in ('X','Y','I','J','R') for k,_ in ws):
            continue
        motion=motion_mode
        vals={k:v for k,v in ws if k!='G'}
        tx=x; ty=y
        if 'X' in vals: tx=(vals['X']*unit if absolute else x+vals['X']*unit)
        if 'Y' in vals: ty=(vals['Y']*unit if absolute else y+vals['Y']*unit)
        if not have_pos:
            x,y=tx,ty; have_pos=True
            if motion!=0: current=[(x,y)]
            continue
        start=(x,y); end=(tx,ty)
        if motion==0:
            flush(); x,y=end; continue
        if not current: current=[start]
        if motion==1 or _dist(start,end)<1e-12:
            current.append(end)
        else:
            clockwise=(motion==2)
            center=None; sweep=None
            if 'I' in vals or 'J' in vals:
                cx=x+vals.get('I',0.0)*unit
                cy=y+vals.get('J',0.0)*unit
                a0=math.atan2(y-cy,x-cx); a1=math.atan2(ty-cy,tx-cx)
                if clockwise:
                    while a1>=a0: a1-=2*math.pi
                else:
                    while a1<=a0: a1+=2*math.pi
                center=(cx,cy); sweep=a1-a0
            elif 'R' in vals:
                rr=arc_center_from_r(start,end,vals['R']*unit,clockwise)
                if rr:
                    center,sweep=rr
            if center is None or sweep is None:
                current.append(end)
            else:
                cx,cy=center
                r=max(1e-12,math.hypot(x-cx,y-cy))
                a0=math.atan2(y-cy,x-cx)
                n=max(8,min(2400,int(abs(sweep)*r/0.8)+1))
                for i in range(1,n+1):
                    a=a0+sweep*i/n
                    current.append((cx+r*math.cos(a),cy+r*math.sin(a)))
                current[-1]=end
        x,y=end
    flush()
    if not paths:
        raise ValueError("No drawable G1/G2/G3 XY geometry found in G-code")
    _gcode_paths.last_stats={"gcode_paths":len(paths),"gcode_modal":1}
    return paths

def _moving_average_path(path: List[Point], passes: int=0) -> List[Point]:
    """Gentle geometry smoothing without changing endpoints."""
    pts=list(path)
    passes=max(0,min(int(passes),6))
    for _ in range(passes):
        if len(pts)<3:
            break
        nxt=[pts[0]]
        for i in range(1,len(pts)-1):
            x=(pts[i-1][0]+2*pts[i][0]+pts[i+1][0])/4.0
            y=(pts[i-1][1]+2*pts[i][1]+pts[i+1][1])/4.0
            nxt.append((x,y))
        nxt.append(pts[-1])
        pts=nxt
    return pts


def _transform_paths(paths: List[List[Point]], rotation_deg: float=0.0,
                     offset_x: float=0.0, offset_y: float=0.0) -> List[List[Point]]:
    """Rotate and offset normalized artwork inside the table."""
    a=math.radians(float(rotation_deg))
    ca,sa=math.cos(a),math.sin(a)
    ox=max(-0.75,min(0.75,float(offset_x)))
    oy=max(-0.75,min(0.75,float(offset_y)))
    out=[]
    for path in paths:
        q=[]
        for x,y in path:
            q.append((x*ca-y*sa+ox, x*sa+y*ca+oy))
        out.append(q)
    return out


def _nearest_route_cost(paths: List[List[Point]]) -> float:
    ordered=_nearest_order(paths)
    if not ordered:
        return 0.0
    total=0.0
    for a,b in zip(ordered,ordered[1:]):
        total += _dist(a[-1],b[0])
    return total


def _choose_start_path(paths: List[List[Point]], start_mode: str="auto") -> List[List[Point]]:
    """
    Reorder the first drawable island. 'perimeter' prefers geometry nearest the
    circular edge; 'center' prefers geometry nearest the origin; 'auto' chooses
    whichever gives the lower nearest-neighbour connector cost.
    """
    paths=[p[:] for p in paths if len(p)>1]
    if len(paths)<2:
        return paths

    def score_center(p):
        a=min(_dist((0.0,0.0),p[0]),_dist((0.0,0.0),p[-1]))
        return a

    def score_perimeter(p):
        ra=max(math.hypot(*p[0]),math.hypot(*p[-1]))
        return -ra

    mode=(start_mode or "auto").lower()
    if mode=="center":
        idx=min(range(len(paths)),key=lambda i:score_center(paths[i]))
    elif mode=="perimeter":
        idx=min(range(len(paths)),key=lambda i:score_perimeter(paths[i]))
    else:
        # compare center/perimeter candidates by total connector cost
        ci=min(range(len(paths)),key=lambda i:score_center(paths[i]))
        pi=min(range(len(paths)),key=lambda i:score_perimeter(paths[i]))
        candidates=[]
        for idx0 in {ci,pi}:
            test=[paths[idx0]]+[p for j,p in enumerate(paths) if j!=idx0]
            candidates.append((_nearest_route_cost(test),idx0))
        idx=min(candidates)[1]
    return [paths[idx]]+[p for j,p in enumerate(paths) if j!=idx]


def _rdp(points: List[Point], epsilon: float) -> List[Point]:
    """Ramer-Douglas-Peucker simplification."""
    if len(points)<3 or epsilon<=0:
        return points[:]
    a,b=points[0],points[-1]
    vx,vy=b[0]-a[0],b[1]-a[1]
    denom=math.hypot(vx,vy)
    best_d=-1.0; best_i=0
    for i,p in enumerate(points[1:-1],1):
        if denom<1e-12:
            d=_dist(a,p)
        else:
            d=abs(vy*p[0]-vx*p[1]+b[0]*a[1]-b[1]*a[0])/denom
        if d>best_d:
            best_d=d;best_i=i
    if best_d>epsilon:
        left=_rdp(points[:best_i+1],epsilon)
        right=_rdp(points[best_i:],epsilon)
        return left[:-1]+right
    return [a,b]


def convert_upload_to_thr(path: Path, threshold: int=128, invert: bool=False, fit: float=.94,
                          smoothing: int=1, simplify: float=0.0025,
                          rotation_deg: float=0.0, offset_x: float=0.0, offset_y: float=0.0,
                          max_bridge: float=0.055, start_mode: str="auto",
                          preserve_all: bool=True, machine_step: float=0.012):
    """
    Professional machine-oriented artwork -> THR pipeline.

    The preview coordinates and saved THR are generated from this exact final
    route, so preview == saved file == machine path.
    """
    ext=path.suffix.lower()
    if ext==".thr":
        pts=[]
        for line in path.read_text(encoding="utf-8",errors="ignore").splitlines():
            line=line.strip()
            if not line or line.startswith("#"): continue
            sp=line.replace(","," ").split()
            if len(sp)>=2:
                try:
                    t=float(sp[0]); r=float(sp[1])
                    if math.isfinite(t) and math.isfinite(r):
                        pts.append((t,max(0.0,min(1.0,r))))
                except Exception:
                    pass
        if len(pts)<2:
            raise ValueError("THR file has too few valid points")
        stats={"source":"thr","route_points":len(pts),"skipped_islands":0}
        stats.update(_validate_thr(pts))
        return pts,stats

    if ext==".svg":
        paths=_svg_paths(path)
    elif ext==".dxf":
        paths=_dxf_paths(path)
    elif ext in {".png",".jpg",".jpeg",".webp",".bmp"}:
        paths=_raster_paths(path,threshold,invert)
    elif ext in {".gcode",".nc",".ngc",".tap"}:
        paths=_gcode_paths(path)
    else:
        raise ValueError("Supported formats: PNG/JPG, SVG, DXF, GCODE/NC/NGC/TAP, THR")

    if not paths:
        raise ValueError("No usable artwork geometry was detected")

    # Keep artwork inside a reserved travel lane. Even if the user requests
    # 98%, cap artwork slightly lower when preserving all disconnected islands.
    requested_fit=max(.55,min(float(fit),.98))
    effective_fit=min(requested_fit,.94) if preserve_all else requested_fit
    paths=_normalize(paths,effective_fit)
    paths=_transform_paths(paths,rotation_deg,offset_x,offset_y)

    smooth=max(0,min(int(smoothing),6))
    paths=[_moving_average_path(q,smooth) for q in paths]

    simp=max(0.0,min(float(simplify),0.025))
    if simp>0:
        paths=[_rdp(q,simp) if len(q)>3 else q for q in paths]

    # Circular boundary verification after transforms.
    clipped=[]
    clipped_points=0
    for q in paths:
        clean=[]
        for x,y in q:
            r=math.hypot(x,y)
            if r<=effective_fit+0.015:
                clean.append((x,y))
            else:
                clipped_points+=1
        if len(clean)>1:
            clipped.append(_dedupe(clean))

    if not clipped:
        raise ValueError("Artwork falls outside the table after positioning")

    bridge=max(0.0,min(float(max_bridge),0.20))
    route,join_stats=_join_clean(
        clipped,
        max_bridge=bridge,
        start_mode=start_mode,
        preserve_all=bool(preserve_all),
        lane_radius=.985,
    )
    if len(route)<2:
        raise ValueError("Could not create a continuous machine route")

    # Real-machine smoothing: cap Cartesian spacing before polar conversion.
    route=_resample_polyline(route,machine_step)
    thr=_densify_thr(_xy_to_thr(route),0.11,0.012)
    validation=_validate_thr(thr)

    stats={
        "source":ext.lstrip("."),
        "route_points":len(thr),
        "input_paths":len(paths),
        "retained_paths":len(clipped),
        "clipped_points":clipped_points,
        "smoothing":smooth,
        "simplify":round(simp,5),
        "rotation_deg":round(float(rotation_deg),2),
        "max_bridge":round(bridge,4),
        "start_mode":start_mode,
        "preserve_all":1 if preserve_all else 0,
        "requested_fit":round(requested_fit,3),
        "effective_fit":round(effective_fit,3),
        "machine_step":round(max(.003,min(.035,float(machine_step))),4),
    }
    stats.update(join_stats)
    stats.update(validation)
    if ext in {".png",".jpg",".jpeg",".webp",".bmp"}:
        stats.update(getattr(_raster_paths,"last_stats",{}) or {})
    elif ext in {".gcode",".nc",".ngc",".tap"}:
        stats.update(getattr(_gcode_paths,"last_stats",{}) or {})
    return thr,stats


def thr_text(points):
    return "\n".join(f"{t:.7f} {r:.7f}" for t,r in points)+"\n"
