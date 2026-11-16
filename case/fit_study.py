# Speaker case dimension-fit blockout, OCTAGONAL. Units mm. X = long axis, Y = front(-)/back(+), Z up.
# Section = rectangle W x H with 45-degree chamfers c: flat top (lid), flat front (PRs), flat back (USB-C, switch).
import bpy, math, sys
from mathutils import Vector

W, H, C = 120.7, 120.7, 35.4   # REGULAR octagon (side 50): across flats 120.7, chamfer 35.4; front/back/top/bottom flats are 50 wide
WALL = 2.5
DRV, DRV_D = 50.0, 25.0
PR_W, PR_H, PR_T = 90.0, 50.0, 6.0
PCB, BAT, BOOST = (100.0, 55.0, 1.6), (100.0, 60.0, 11.0), (67.2, 43.8, 16.0)
TP, ESP, AMP, SW_D = (28.0, 17.0, 5.0), (55.0, 28.0, 13.0), (17.78, 19.05, 6.0), 20.0
PCB_HOLES = [(sx*46.0, sy*23.5) for sx in (-1,1) for sy in (-1,1)]   # from Speaker4.kicad_pcb: 2.7 mm holes, 92 x 47 mm
BOOST_HOLES = (67.2-2*3.5, 43.8-2*3.5)   # HW-317 V6: board 67.2 x 43.8, 3.0 mm holes (user); centre spacing ASSUMED 3.5 mm inset, measure
L = 216.0
DOME_X = 0.3*(DRV/2 + 8)
CHAMBER = DRV_D + 2*WALL + 4
BODY_L = PCB[0] + 6

def oct_pts(w, h, c):
    a, b = w/2, h/2
    return [(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)]
Wi, Hi, Ci = W-2*WALL, H-2*WALL, C - 2*WALL + WALL*math.sqrt(2)
KI = Wi/2 + Hi/2 - Ci
def inside_inner(y, z):
    return abs(y) <= Wi/2+1e-6 and abs(z) <= Hi/2+1e-6 and abs(y)+abs(z) <= KI+1e-6

bpy.ops.wm.read_factory_settings(use_empty=True)
cols = dict(shell=(.6,.7,.9,.25), pcb=(.1,.5,.2,1), bat=(.8,.3,.1,1), boost=(.2,.3,.8,1), tp=(.7,.1,.6,1),
            esp=(.1,.1,.1,1), amp=(.9,.8,.1,1), drv=(.9,.9,.9,1), pr=(.9,.4,.4,1), sw=(0,.8,.8,1))
M = {}
for k, c in cols.items():
    m = bpy.data.materials.new(k); m.diffuse_color = c; M[k] = m

def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object
    o.name = name; o.scale = size; o.data.materials.append(M[m]); return o
def cyl(name, r, d, loc, rot, m):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot); o = bpy.context.object
    o.name = name; o.data.materials.append(M[m]); return o

# octagonal prism along X
pts = oct_pts(W, H, C); n = len(pts)
verts = [(-L/2, y, z) for y, z in pts] + [(L/2, y, z) for y, z in pts]
faces = [list(range(n))[::-1], [n+i for i in range(n)]] + [[i, (i+1)%n, n+(i+1)%n, n+i] for i in range(n)]
me = bpy.data.meshes.new("shell"); me.from_pydata(verts, [], faces); me.update()
shell = bpy.data.objects.new("shell_oct", me); bpy.context.collection.objects.link(shell)
shell.data.materials.append(M['shell']); shell.display_type = 'WIRE'

parts = []
Z0 = -H/2 + WALL                  # floor top
ZT = H/2 - WALL                   # ceiling (lid underside)
yw = W/2
# ---------- FLOOR: HW-317 boost on 4 short snap posts ----------
POST_B = 5.0
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(cyl(f"post_boost{sx}{sy}", 3.0, POST_B, (sx*BOOST_HOLES[0]/2, sy*BOOST_HOLES[1]/2, Z0+POST_B/2), (0,0,0), 'tp'))
parts.append(box("boost_HW317", BOOST, (0, 0, Z0 + POST_B + BOOST[2]/2), 'boost'))
boost_top = Z0 + POST_B + BOOST[2]
# ---------- ABOVE IT: PCB on 4 tall floor posts that straddle the boost (holes at x +-46, boost only reaches +-33.6) ----------
PCB_GAP = 3.0
z_pcb_bot = boost_top + PCB_GAP
POST_H = z_pcb_bot - Z0
z_pcb = z_pcb_bot + PCB[2]/2; z_top_pcb = z_pcb_bot + PCB[2]
parts.append(box("pcb", PCB, (0, 0, z_pcb), 'pcb'))
for i, (hx, hy) in enumerate(PCB_HOLES):
    parts.append(cyl(f"post_pcb{i}", 4.0, POST_H, (hx, hy, Z0+POST_H/2), (0,0,0), 'tp'))
    parts.append(cyl(f"pin_pcb{i}", 1.4, PCB[2]+1.3, (hx, hy, z_pcb_bot+(PCB[2]+1.3)/2), (0,0,0), 'tp'))
parts.append(box("esp32", ESP, (-25, 0, z_top_pcb + ESP[2]/2), 'esp'))
parts.append(box("amp_U1", AMP, (22, -12, z_top_pcb + AMP[2]/2), 'amp'))
parts.append(box("amp_U2", AMP, (22, 12, z_top_pcb + AMP[2]/2), 'amp'))
# ---------- TP4056 + USB-C on the back flat at +x, on posts that grow from the lower slope ----------
X_TP = 64.0; TP_Z = -18.0
parts.append(box("tp4056", (TP[1], TP[0], TP[2]), (X_TP, yw - WALL - TP[0]/2, TP_Z), 'tp'))
y_post = yw - WALL - 6.0; z_slope = -(KI - y_post)           # where the lower slope is at that y
for sx in (-1, 1):
    h = (TP_Z - TP[2]/2) - z_slope
    parts.append(box(f"tp_cradle{sx}", (2.0, 8.0, h), (X_TP + sx*(TP[1]/2+1.0), y_post, z_slope + h/2), 'sw'))
parts.append(box("usbc_port", (9, WALL+1, 3.5), (X_TP, yw - WALL/2, TP_Z + 1.5), 'sw'))
SW_DEPTH = 14.0
parts.append(cyl("switch_20mm", SW_D/2, SW_DEPTH, (-68.0, yw - WALL - SW_DEPTH/2 + 1, 0.0), (math.radians(90), 0, 0), 'sw'))
# ---------- CEILING (lid): the top flat is only ~48 mm wide inside, so a 60 mm battery hangs lower in a cradle on 2 hanger arms from the lid ----------
CL = 0.3; TW = 1.6; CLIP_H = 8.0; PLATE = 2.0
bat_top = ZT - 9.5; bat_bot = bat_top - BAT[2]; bat_z = bat_top - BAT[2]/2
parts.append(box("battery", BAT, (0, 0, bat_z), 'bat'))
parts.append(box("tray_plate", (BAT[0]+2*CL+2*TW, BAT[1]+2*CL+2*TW, PLATE), (0, 0, bat_bot - PLATE/2), 'sw'))
for sy in (-1, 1):
    parts.append(box(f"tray_clip_y{sy}", (BAT[0]+2*CL+2*TW, TW, CLIP_H), (0, sy*(BAT[1]/2+CL+TW/2), bat_bot + CLIP_H/2 - 2.0), 'sw'))
for sx in (-1, 1):
    parts.append(box(f"tray_clip_x{sx}", (TW, BAT[1]+2*CL, CLIP_H), (sx*(BAT[0]/2+CL+TW/2), 0, bat_bot + CLIP_H/2 - 2.0), 'sw'))
    hx = BAT[0]/2 + CL + TW + 1.5
    parts.append(box(f"tray_hanger{sx}", (3.0, 20.0, ZT - (bat_bot - PLATE)), (sx*hx, 0, (ZT + bat_bot - PLATE)/2), 'sw'))
# battery lead: from the battery down to the PCB's JST (board-relative -2.25, -22.5), unplugs when the lid is lifted
cab_top = bat_bot; cab_bot = z_top_pcb
parts.append(cyl("cable_battery", 1.5, cab_top - cab_bot, (-2.25, -22.5, (cab_top+cab_bot)/2), (0,0,0), 'sw'))
for s, side in ((-1, "L"), (1, "R")):
    parts.append(box(f"driver_{side}", (DRV_D, DRV, DRV), (s*(L/2 - DRV_D/2 - WALL), 0, 0), 'drv'))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=DRV/2+8, location=(s*(L/2), 0, 0)); d = bpy.context.object
    d.name = f"dome_{side}"; d.scale = (0.3, 1, 1); d.data.materials.append(M['shell']); d.display_type = 'WIRE'
    parts.append(box(f"PR_{side}", (PR_W, PR_T, PR_H), (s*(PR_W/2 + 2), -W/2 + PR_T/2 - 1, 0), 'pr'))
shelf1_dummy = None
SH1_Z = SH2_Z = 0; SH_T = 0
print("outer %.0f x %.0f x %.0f (L x W x H), with domes L=%.0f (limit 240); front/back flat %.0f tall" % (L, W, H, L+2*DOME_X, H-2*C))
def aabb(o):
    d = (SW_D, SW_DEPTH, SW_D) if o.name.startswith('switch') else tuple(o.dimensions)
    return [(o.location[i]-d[i]/2, o.location[i]+d[i]/2) for i in range(3)]
for o in parts:
    if o.name.startswith(("pcb","battery","boost","tp4056","esp","amp","driver","switch","tray","bridge","post","tp_cradle")):
        (x0,x1),(y0,y1),(z0,z1) = aabb(o)
        zs = (z1,) if o.name.startswith(('post','tp_cradle')) else (z0,z1)
        ok = all(inside_inner(y, z) for y in (y0,y1) for z in zs) and abs(x0)<=L/2 and abs(x1)<=L/2
        if not ok and not o.name.startswith("switch"): print("OUTSIDE inner section:", o.name)
sup = ("tray","bridge","post","pin","tp_cradle","usbc","dome","PR","pcb_","shell")
internals = [o for o in parts if not o.name.startswith(("tray","bridge","post","pin","tp_cradle","usbc","PR"))]
supports = [o for o in parts if o.name.startswith(("tray","bridge","post","pin","tp_cradle","cable"))]
def hit(a, b): return all(p[0] < q[1]-0.05 and q[0] < p[1]-0.05 for p, q in zip(aabb(a), aabb(b)))
for i, a in enumerate(internals):
    for b in internals[i+1:]:
        if {a.name, b.name} <= {"pcb","esp32","amp_U1","amp_U2"}: continue
        if hit(a, b): print("COLLISION:", a.name, b.name)
allp = [o for o in parts if not o.name.startswith(("usbc","PR"))]
for i, a in enumerate(allp):
    for b in allp[i+1:]:
        if a in internals and b in internals: continue
        if a.name.startswith(("tray_","bridge","tp_cradle","post","pin","cable")) and b.name.startswith(("tray_","bridge","tp_cradle","post","pin","cable")): continue
        if {a.name, b.name} & {"battery"} and (a.name.startswith("tray") or b.name.startswith("tray")): continue
        if hit(a, b): print("SUPPORT HIT:", a.name, b.name)
print("PCB hole centres vs board: holes at (+-46, +-23.5), 4 posts d7 x 6 high, pins d2.4 w/ 3.1 barb (see mount_coupon.py)")
print("boost top z=%.1f  PCB bottom z=%.1f (posts %.1f tall)  PCB deck top z=%.1f  battery bottom z=%.1f  lid inner z=%.1f  free air %.1f" % (boost_top, z_pcb_bot, POST_H, z_top_pcb+ESP[2], bat_top-BAT[2], ZT, bat_top-BAT[2]-(z_top_pcb+ESP[2])))

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1400, 800
w = bpy.data.worlds.new("w"); w.color = (.9,.9,.92); sc.world = w
out = sys.argv[sys.argv.index("--")+1]
for name, loc in (("back", (0, 380, 100)), ("iso", (260, -300, 200)), ("top", (0, 0, 380)), ("end", (330, 0, 20))):
    bpy.ops.object.camera_add(location=loc); cam = bpy.context.object
    cam.rotation_euler = (Vector((0,0,0)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = 2000
    if name == "top": cam.data.type = 'ORTHO'; cam.data.ortho_scale = 260
    sc.camera = cam; sc.render.filepath = f"{out}/fit_{name}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/fit_study.blend")
