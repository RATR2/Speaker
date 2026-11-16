# Printable speaker case: body.stl + lid.stl (print-orientation). Units mm. X long axis, Y front(-)/back(+), Z up.
# Regular octagon section 120.7 across flats (flats 50 wide), floor/ceiling-supported internals (see fit_study.py).
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--")+1]
FLAT = 51.0; W = H = FLAT*(1+math.sqrt(2)); A_ = W/2;   # 51 mm flats: 90x50 PR (1 mm thick) + clearance
C = A_ - FLAT/2          # chamfer 35.35
WALL = 2.5; L = 216.0; A = 10.0                                  # body length, dome bulge
Wi = W - 2*WALL; Ci = C - 2*WALL + WALL*math.sqrt(2)
ZB = -(H/2 - WALL); ZT = H/2 - WALL                              # floor / ceiling inner surfaces (+-57.85)
ZC = FLAT/2                                                      # body/lid split plane z = 25
PCB = (100.0, 55.0, 1.6); BAT = (100.0, 60.0, 11.0); BOOST = (67.2, 43.8, 16.0); TP = (28.0, 17.0, 5.0)
PCB_HOLES = [(sx*46.0, sy*23.5) for sx in (-1,1) for sy in (-1,1)]
BOOST_HOLES = (67.2-7.0, 43.8-7.0)                               # ASSUMED 3.5 mm edge inset; measure the real module
SW_D = 20.4; DRV = 50.0; DRV_D = 30.0; DRV_CONE = 44.0   # driver 50 x 50 x 30 mm (user); cone hole size is an assumption
EPS = 0.01

bpy.ops.wm.read_factory_settings(use_empty=True)
def link(o): bpy.context.collection.objects.link(o); return o
def mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); return link(bpy.data.objects.new(name, me))
def oct_pts(w, h, c):
    a, b = w/2, h/2
    return [(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)]
def prism(name, pts, x0, x1):
    n = len(pts); v = [(x0,y,z) for y,z in pts] + [(x1,y,z) for y,z in pts]
    f = [list(range(n))[::-1], [n+i for i in range(n)]] + [[i,(i+1)%n,n+(i+1)%n,n+i] for i in range(n)]
    o = mesh_obj(name, v, f); return o
def box(name, x0,x1,y0,y1,z0,z1):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (x1-x0, y1-y0, z1-z0); o.location = ((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
    bpy.context.view_layer.update(); apply_xf(o); return o
def apply_xf(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
def cyl_axis(name, axis, r, c0, c1, center, seg=48):
    """cylinder along 'x'|'y'|'z' from coordinate c0 to c1; center=(other two coords)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=abs(c1-c0)); o = bpy.context.object; o.name = name
    mid = (c0+c1)/2
    if axis == 'x': o.rotation_euler = (0, math.radians(90), 0); o.location = (mid, center[0], center[1])
    elif axis == 'y': o.rotation_euler = (math.radians(90), 0, 0); o.location = (center[0], mid, center[1])
    else: o.location = (center[0], center[1], mid)
    bpy.context.view_layer.update(); apply_xf(o); return o
def ellipsoid(name, cx, rx, ry, rz):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); o = bpy.context.object; o.name = name
    o.scale = (rx, ry, rz); o.location = (cx, 0, 0); bpy.context.view_layer.update(); apply_xf(o); return o
def boolean(a, b, op, delete_b=True):
    m = a.modifiers.new("b", 'BOOLEAN'); m.object = b; m.operation = op; m.solver = 'EXACT'; m.use_self = True
    bpy.context.view_layer.objects.active = a; bpy.ops.object.modifier_apply(modifier=m.name)
    if delete_b: bpy.data.objects.remove(b, do_unlink=True)
    return a
def union_all(objs, name):
    objs = [o for o in objs if o]
    base = objs[0]
    for o in objs[1:]:
        boolean(base, o, 'UNION')
    base.name = name; return base
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = name; return objs[0]
def nonmanifold(o):
    bm = bmesh.new(); bm.from_mesh(o.data); n = sum(not e.is_manifold for e in bm.edges); bm.free(); return n

# ---------------- 1. hollow octagonal shell with domed ends ----------------
Rd = 66.5
outer = prism("outer", oct_pts(W, H, C), -L/2, L/2)
for s in (-1, 1):
    ext = prism("ext", oct_pts(W, H, C), s*L/2 - (0 if s > 0 else A+1), s*L/2 + (A+1 if s > 0 else 0))
    cap = boolean(ext, ellipsoid("e", s*L/2, A, Rd, Rd), 'INTERSECT')
    boolean(outer, cap, 'UNION')
inner = prism("inner", oct_pts(Wi, Wi, Ci), -(L/2-WALL), L/2-WALL)
for s in (-1, 1):
    x0 = s*(L/2-WALL)
    ext = prism("ext", oct_pts(Wi, Wi, Ci), x0 - (0 if s > 0 else A+1), x0 + (A+1 if s > 0 else 0))
    cap = boolean(ext, ellipsoid("e", x0, A, Rd-WALL, Rd-WALL), 'INTERSECT')
    boolean(inner, cap, 'UNION')
shell = boolean(outer, inner, 'DIFFERENCE')
shell.name = "shell"
print("shell non-manifold:", nonmanifold(shell))

# driver seats: square tube (50.6 inner, 55 outer) fused into each dome, driver slides in from behind; cone hole through the dome crown
for s in (-1, 1):
    xa, xb = sorted((s*(L/2 - WALL - DRV_D), s*(L/2 + A - 1.5)))
    tube = box("tube", xa, xb, -27.5, 27.5, -27.5, 27.5)
    boolean(tube, box("tin", xa-1, xb+1, -25.3, 25.3, -25.3, 25.3), 'DIFFERENCE')
    boolean(shell, tube, 'UNION')
for s in (-1, 1):
    boolean(shell, cyl_axis("cone", 'x', DRV_CONE/2, s*(L/2-3), s*(L/2+A+3), (0, 0)), 'DIFFERENCE')
print("shell+seats non-manifold:", nonmanifold(shell))

# ---------------- 2. split into body and lid at z = ZC ----------------
lidbox = box("lidbox", -L, L, -90, 90, ZC, 90)
lid = shell.copy(); lid.data = shell.data.copy(); link(lid); lid.name = "lid"
boolean(lid, lidbox, 'INTERSECT', delete_b=False)
body = shell; body.name = "body"
boolean(body, lidbox, 'DIFFERENCE')

# ---------------- 3. snap pin posts ----------------
def snap_post(name, x, y, z0, post_r, post_h, shank_d, board_t, slot=0.8, barb_over=0.35, tip_len=3.0, rt=0.9, slot_from=0.3, slot_normal='x', rot=None):
    rs = shank_d/2; rb = rs + barb_over; zl = board_t + 0.15; zt = zl + tip_len
    prof = [(0,-1),(post_r,-1),(post_r,post_h),(rs,post_h),(rs,post_h+zl),(rb,post_h+zl),(rt,post_h+zt),(0,post_h+zt)]
    bm = bmesh.new(); vs = [bm.verts.new((r,0,z)) for r, z in prof]; es = [bm.edges.new((vs[i], vs[i+1])) for i in range(len(vs)-1)]
    bmesh.ops.spin(bm, geom=vs+es, cent=(0,0,0), axis=(0,0,1), angle=2*math.pi, steps=48)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = link(bpy.data.objects.new(name, me))
    zs0, zs1 = post_h+slot_from, post_h+zt+2
    big = 2*rb + 4
    cut = box("slot", -slot/2, slot/2, -big/2, big/2, zs0, zs1) if slot_normal == 'x' else box("slot", -big/2, big/2, -slot/2, slot/2, zs0, zs1)
    boolean(o, cut, 'DIFFERENCE')
    if rot: o.rotation_euler = rot
    o.location = (x, y, z0); apply_xf(o)
    return o
adds = []
def safe_prism():
    w_in = 0.5
    return prism("safe", oct_pts(W-2*w_in, H-2*w_in, C-2*w_in+w_in*math.sqrt(2)), -L/2, L/2)   # outer octagon inset 0.5 mm: nothing may poke through the skin
Z_PCB_BOT = ZB + 5.0 + BOOST[2] + 3.0                    # PCB sits 3 mm above the boost module top
posts = []
for i, (hx, hy) in enumerate(PCB_HOLES):
    posts.append(snap_post(f"pcbpost{i}", hx, hy, ZB, 4.0, Z_PCB_BOT - ZB, 2.4, PCB[2], slot=0.8, tip_len=3.0, slot_from=0.3))
for sx in (-1, 1):
    for sy in (-1, 1):
        posts.append(snap_post(f"boostpost{sx}{sy}", sx*BOOST_HOLES[0]/2, sy*BOOST_HOLES[1]/2, ZB, 3.5, 5.0, 2.7, 1.6, slot=0.8, tip_len=3.0, slot_from=0.3))
pg = join(posts, "postgrp"); boolean(pg, safe_prism(), 'INTERSECT'); adds.append(pg)    # tower bases were poking out through the lower corners
# TP4056 (no mounting holes): flat platform on two ribs, rear stop wall, two side pegs, strap slots
KI = Wi/2 + Wi/2 - Ci
X_TP, TP_Z = 64.0, -18.0
Y_WIN = W/2 - WALL                                       # back wall inner face
TP_BOT = TP_Z - TP[2]/2                                  # underside of the board
PL_T, PL_HW, PL_Y0 = 2.0, 14.5, Y_WIN - TP[0] - 2.0      # platform half-width, rear edge (leaves room for the stop wall)
tpp = [box("tp_plate", X_TP-PL_HW, X_TP+PL_HW, PL_Y0, Y_WIN+0.5, TP_BOT-PL_T, TP_BOT)]
for sx in (-1, 1):
    tpp.append(box(f"tp_rib{sx}", X_TP+sx*7.0-1.2, X_TP+sx*7.0+1.2, PL_Y0+2, Y_WIN-1, -KI+PL_Y0-1, TP_BOT-PL_T+0.3))
tpp.append(box("tp_stop", X_TP-9.0, X_TP+9.0, PL_Y0, PL_Y0+1.6, TP_BOT, TP_BOT+3.5))          # small wall at the rear end of the board
ypc = Y_WIN - TP[0]/2
for sx in (-1, 1):
    tpp.append(box(f"tp_peg{sx}", X_TP+sx*(TP[1]/2+0.4)+(0 if sx > 0 else -1.6), X_TP+sx*(TP[1]/2+0.4)+(1.6 if sx > 0 else 0), ypc-4, ypc+4, TP_BOT, TP_BOT+3.8))
tg = join(tpp, "tpgrp")
for sx in (-1, 1):   # strap slots (cable tie / velcro) either side of the board
    boolean(tg, box(f"strapslot{sx}", X_TP+sx*12.0-1.5, X_TP+sx*12.0+1.5, ypc-3, ypc+3, TP_BOT-PL_T-1, TP_BOT+1), 'DIFFERENCE')
boolean(tg, safe_prism(), 'INTERSECT'); adds.append(tg)
# switch housing: tube around the switch body + terminals, closed inner end with a wire slot at the bottom
SW_X = -68.0; Y_WALL_IN = W/2 - WALL; HOUS_ID, HOUS_T, HOUS_LEN = 23.0, 1.6, 22.0
hous = cyl_axis("hous", 'y', HOUS_ID/2+HOUS_T, Y_WALL_IN-HOUS_LEN, Y_WALL_IN+1.0, (SW_X, 0.0))
boolean(hous, cyl_axis("housin", 'y', HOUS_ID/2, Y_WALL_IN-HOUS_LEN+HOUS_T, Y_WALL_IN+2.0, (SW_X, 0.0)), 'DIFFERENCE')
boolean(hous, box("wireslot", SW_X-5, SW_X+5, Y_WALL_IN-HOUS_LEN-1, Y_WALL_IN-HOUS_LEN+HOUS_T+1, -HOUS_ID/2-HOUS_T-1, -3.0), 'DIFFERENCE')
adds.append(hous)
# base skirt so it cannot roll on its 50 mm bottom flat
adds.append(box("skirt", -75, 75, -50, 50, -H/2-3.0, -H/2+0.5))
body = boolean(body, join(adds, "adds"), 'UNION')

# ---------------- 4. hinge (back, +Y) with a 1.75 mm filament pin ----------------
HAX_Y, HAX_Z, HR = W/2 + 5.0, ZC + 2.5, 4.6
SEG, GAP = 14.0, 0.6
x_start = -(5*SEG + 4*GAP)/2
bk, lk = [], []
for k in range(5):
    x0 = x_start + k*(SEG+GAP); x1 = x0 + SEG
    barrel = cyl_axis(f"kn{k}", 'x', HR, x0, x1, (HAX_Y, HAX_Z))
    if k % 2 == 0:   # body knuckle: arm down to the back wall
        arm = box(f"arm{k}", x0, x1, W/2 - 3.0, HAX_Y, ZC - 12.0, ZC - 0.5)
        bk += [barrel, arm]
    else:            # lid knuckle: arm into the lid's back chamfer, kept above the body top
        arm = box(f"arm{k}", x0, x1, W/2 - 8.0, HAX_Y, ZC + 0.6, HAX_Z + HR*0.6)
        lk += [barrel, arm]
body = boolean(body, join(bk, "bk"), 'UNION')
lid = boolean(lid, join(lk, "lk"), 'UNION')
for o in (body, lid):
    boolean(o, cyl_axis("pin", 'x', 1.0, -50, 50, (HAX_Y, HAX_Z), seg=24), 'DIFFERENCE')

# ---------------- 5. lid: battery cradle on two hanger arms + front snap tabs ----------------
CL, TW, CLIP_H, PLATE = 0.3, 1.6, 8.0, 2.0
bat_top = ZT - 9.5; bat_bot = bat_top - BAT[2]
la = [box("plate", -(BAT[0]/2+CL+TW), BAT[0]/2+CL+TW, -(BAT[1]/2+CL+TW), BAT[1]/2+CL+TW, bat_bot-PLATE, bat_bot)]
for sy in (-1, 1):
    y0 = sy*(BAT[1]/2+CL); y1 = sy*(BAT[1]/2+CL+TW)
    la.append(box(f"cy{sy}", -(BAT[0]/2+CL+TW), BAT[0]/2+CL+TW, min(y0,y1), max(y0,y1), bat_bot-PLATE, bat_bot+CLIP_H-2.0))
for sx in (-1, 1):
    x0 = sx*(BAT[0]/2+CL); x1 = sx*(BAT[0]/2+CL+TW)
    la.append(box(f"cx{sx}", min(x0,x1), max(x0,x1), -(BAT[1]/2+CL), BAT[1]/2+CL, bat_bot-PLATE, bat_bot+CLIP_H-2.0))
    hx = BAT[0]/2 + CL + TW + 1.5
    la.append(box(f"hang{sx}", sx*hx-1.5, sx*hx+1.5, -10, 10, bat_bot-PLATE, ZT+1.0))
# front snap tabs (x = +-40) hanging inside the front wall, hooks engage windows in the body wall
for sx in (-1, 1):
    xc = sx*99.0
    la.append(box(f"tab{sx}", xc-6, xc+6, -(W/2-WALL)+1.35, -(W/2-WALL)+1.35+1.6, ZC-13.0, ZC+1.0))
    hook = mesh_obj(f"hook{sx}", [(xc-6,-(W/2-WALL)+1.35, ZC-13.0), (xc-6,-(W/2-WALL)+1.35-2.0, ZC-13.0+2.0), (xc-6,-(W/2-WALL)+1.35, ZC-13.0+3.4),
                                  (xc+6,-(W/2-WALL)+1.35, ZC-13.0), (xc+6,-(W/2-WALL)+1.35-2.0, ZC-13.0+2.0), (xc+6,-(W/2-WALL)+1.35, ZC-13.0+3.4)],
                    [[0,2,1],[3,4,5],[0,1,4,3],[1,2,5,4],[0,3,5,2]])
    la.append(hook)
lid = boolean(lid, join(la, "la"), 'UNION')
boolean(lid, box("cable", -2.25-5, -2.25+5, -22.5-3, -22.5+3, bat_bot-PLATE-1, bat_bot+1), 'DIFFERENCE')

# ---------------- 6. cut-outs (body) ----------------
cuts = []
for sx in (-1, 1):   # passive radiator openings on the front flat (placeholder 82 x 42, centred 47 mm from the middle)
    # one rectangular opening per radiator, 66 x 45, clear of the 4 snap pins (barbs reach |x|>34.5)
    cuts.append(box(f"pr{sx}", sx*47-33, sx*47+33, -W/2-1, -W/2+WALL+8, -22.5, 22.5))
    cuts.append(box(f"prseat{sx}", sx*47-45.2, sx*47+45.2, -W/2+1.4, -W/2+WALL+1.5, -25.2, 25.2))   # 90 x 50 x 1 mm plate sits in a 1.1 mm recess on the INSIDE of the front wall
    cuts.append(box(f"win{sx}", sx*99-7, sx*99+7, -(W/2-WALL)-1.4, -(W/2-WALL)+1.8, ZC-13.0-0.3, ZC-13.0+4.0))
cuts.append(box("usb", X_TP-5.2, X_TP+5.2, W/2-WALL-1, W/2+1, TP_BOT+1.6-0.4, TP_BOT+1.6+3.3+0.8))   # receptacle sits on the 1.6 mm board, 3.3 tall
cuts.append(cyl_axis("sw", 'y', SW_D/2, W/2-WALL-1, W/2+1, (SW_X, 0.0)))
body = boolean(body, join(cuts, "cuts"), 'DIFFERENCE')
# snap pins for the PR corner holes: round arrow pins on the INSIDE of the front wall, pointing +Y, barbs catch the plate's back face
PR_PIN_D, PR_BARB = 9.2, 10.9          # hole is 10 mm in the short direction (17.5 along the long one)
pins = []
for sx in (-1, 1):
    for dx in (-40.0, 40.0):
        for dz in (-20.0, 20.0):
            pins.append(snap_post(f"prpin{sx}{dx}{dz}", sx*47+dx, -W/2+1.4, dz, 7.0, 0.0, PR_PIN_D, 1.0, slot=3.0, barb_over=(PR_BARB-PR_PIN_D)/2, tip_len=6.0, rt=3.3, slot_from=0.0, slot_normal='y', rot=(-math.pi/2, 0, 0)))
pj = join(pins, "prpins")
w_in = 0.5
boolean(pj, prism("safe", oct_pts(W-2*w_in, H-2*w_in, C-2*w_in+w_in*math.sqrt(2)), -L/2, L/2), 'INTERSECT')
boolean(pj, box("lidbox2", -L, L, -90, 90, ZC, 90), 'DIFFERENCE')   # upper pins stop at the split plane (the plate corner is a notch there anyway)
body = boolean(body, pj, 'UNION')

# ---------------- 7. checks ----------------
for o in (body, lid): print(o.name, "non-manifold edges:", nonmanifold(o), "dims", tuple(round(d,1) for d in o.dimensions), "verts", len(o.data.vertices))
def bvh_of(o, m=Matrix.Identity(4)):
    vs = [m @ v.co for v in o.data.vertices]; return BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in o.data.polygons])
bvh_body = bvh_of(body)
def lid_clash(angle, lift=0.0):
    m = Matrix.Translation((0, 0, lift)) @ Matrix.Translation((0, HAX_Y, HAX_Z)) @ Matrix.Rotation(math.radians(angle), 4, 'X') @ Matrix.Translation((0, -HAX_Y, -HAX_Z))
    return len(bvh_body.overlap(bvh_of(lid, m)))
print("closed lid, lifted 0.1 mm (should be 0):", lid_clash(0, 0.1))
for ang in (-3, -10, -30, -60, -90, -110, -130):
    print("lid opens", ang, "deg -> overlap pairs", lid_clash(ang))
# ---------------- 8. export in print orientation ----------------
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/case_assembly.blend")
def export(o, name, flip=False):
    c = o.copy(); c.data = o.data.copy(); link(c)
    if flip: c.rotation_euler = (math.pi, 0, 0)
    bpy.context.view_layer.update(); apply_xf(c)
    zmin = min(v.co.z for v in c.data.vertices); c.location.z -= zmin; apply_xf(c)
    bpy.ops.object.select_all(action='DESELECT'); c.select_set(True)
    bpy.ops.wm.stl_export(filepath=f"{OUT}/{name}.stl", export_selected_objects=True)
    print(name, "print size", tuple(round(d,1) for d in c.dimensions))
export(body, "speaker_body")
export(lid, "speaker_lid", flip=True)
