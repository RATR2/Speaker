# Speaker case dimension-fit blockout, OCTAGONAL. Units mm. X = long axis, Y = front(-)/back(+), Z up.
# Section = rectangle W x H with 45-degree chamfers c: flat top (lid), flat front (PRs), flat back (USB-C, switch).
import bpy, math, sys
from mathutils import Vector

W, H, C = 96.0, 76.0, 13.0      # outer width (Y), height (Z), chamfer; front/back flat = H-2C = 50 tall
WALL = 2.5
DRV, DRV_D = 50.0, 25.0
PR_W, PR_H, PR_T = 90.0, 50.0, 6.0
PCB, BAT, BOOST = (100.0, 55.0, 1.6), (100.0, 60.0, 11.0), (67.0, 44.0, 16.0)
TP, ESP, AMP, SW_D = (28.0, 17.0, 5.0), (55.0, 28.0, 13.0), (17.78, 19.05, 6.0), 20.0
CHAMBER = DRV_D + 2*WALL + 4
BODY_L = PCB[0] + 6
L = max(BODY_L + 2*CHAMBER, 2*PR_W + 8)
DOME_X = 0.4*(DRV/2 + 8)

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
z_pcb = -H/2 + WALL + 6          # on 6 mm standoffs from the floor
z_top_pcb = z_pcb + PCB[2]/2
parts.append(box("pcb", PCB, (0, 0, z_pcb), 'pcb'))
parts.append(box("esp32", ESP, (-25, 0, z_top_pcb + ESP[2]/2), 'esp'))
parts.append(box("amp_U1", AMP, (22, -12, z_top_pcb + AMP[2]/2), 'amp'))
parts.append(box("amp_U2", AMP, (22, 12, z_top_pcb + AMP[2]/2), 'amp'))
z_bat = z_top_pcb + ESP[2] + 2 + BAT[2]/2
parts.append(box("battery", BAT, (0, 0, z_bat), 'bat'))
z_boost = z_bat + BAT[2]/2 + BOOST[2]/2
parts.append(box("boost_HW317", BOOST, (0, 0, z_boost), 'boost'))
# back flat wall (y = +W/2): USB-C + TP4056 behind it, switch
yw = W/2
tp = box("tp4056", (TP[1], TP[0], TP[2]), (45, yw - WALL - TP[0]/2, z_bat - 8), 'tp'); parts.append(tp)
parts.append(box("usbc_port", (9, WALL+1, 3.5), (45, yw - WALL/2, z_bat - 8), 'sw'))
SW_DEPTH = 14.0
parts.append(cyl("switch_20mm", SW_D/2, SW_DEPTH, (-40, yw - WALL - SW_DEPTH/2 + 1, z_bat + 6), (math.radians(90), 0, 0), 'sw'))
for s, side in ((-1, "L"), (1, "R")):
    parts.append(box(f"driver_{side}", (DRV_D, DRV, DRV), (s*(L/2 - DRV_D/2 - WALL), 0, 0), 'drv'))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=DRV/2+8, location=(s*(L/2), 0, 0)); d = bpy.context.object
    d.name = f"dome_{side}"; d.scale = (0.4, 1, 1); d.data.materials.append(M['shell']); d.display_type = 'WIRE'
    parts.append(box(f"PR_{side}", (PR_W, PR_T, PR_H), (s*(PR_W/2 + 2), -W/2 + PR_T/2 - 1, 0), 'pr'))

print("outer %.0f x %.0f x %.0f (L x W x H), with domes L=%.0f (limit 240); front/back flat %.0f tall" % (L, W, H, L+2*DOME_X, H-2*C))
for o in parts:
    if o.name.startswith(("pcb","battery","boost","tp","esp","amp","driver","switch")):
        dx, dy, dz = o.dimensions; loc = o.location
        if o.name.startswith("switch"): dy, dz = o.dimensions.z if False else o.dimensions.y, o.dimensions.z
        ok = all(inside_inner(loc.y + sy*dy/2, loc.z + sz*dz/2) for sy in (-1,1) for sz in (-1,1))
        if o.name.startswith("switch"):   # rotated: switch rear end sits at y=loc.y-depth/2; face edge reaches the outer wall by design
            ok = inside_inner(loc.y - SW_DEPTH/2, loc.z + SW_D/2) and inside_inner(loc.y - SW_DEPTH/2, loc.z - SW_D/2)
        print(f"{o.name:12s} dims=({dx:.1f},{dy:.1f},{dz:.1f}) inside_inner={ok}")
# real collisions: AABB overlap between non-adjacent internals
def aabb(o):
    if o.name.startswith('switch'): d=(SW_D,SW_DEPTH,SW_D)
    else: d=tuple(o.dimensions)
    return [(o.location[i]-d[i]/2, o.location[i]+d[i]/2) for i in range(3)]
def _old(o): return [(o.location[i]-o.dimensions[i]/2, o.location[i]+o.dimensions[i]/2) for i in range(3)]
internals = [o for o in parts if o.name.split("_")[0] in ("pcb","esp32","amp","battery","boost","tp4056","switch","usbc","driver")]
for i, a in enumerate(internals):
    for b in internals[i+1:]:
        if {a.name, b.name} == {"pcb","esp32"} or a.name.startswith("usbc") or b.name.startswith("usbc"): continue
        if "amp" in a.name and b.name == "pcb" or "amp" in b.name and a.name == "pcb": continue
        if all(p[0] < q[1]-0.05 and q[0] < p[1]-0.05 for p, q in zip(aabb(a), aabb(b))): print("COLLISION:", a.name, b.name)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1400, 800
w = bpy.data.worlds.new("w"); w.color = (.9,.9,.92); sc.world = w
out = sys.argv[sys.argv.index("--")+1]
for name, loc in (("back", (0, 330, 120)), ("iso", (210, -230, 150)), ("top", (0, 0, 380)), ("end", (330, 0, 20))):
    bpy.ops.object.camera_add(location=loc); cam = bpy.context.object
    cam.rotation_euler = (Vector((0,0,0)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = 2000
    if name == "top": cam.data.type = 'ORTHO'; cam.data.ortho_scale = 260
    sc.camera = cam; sc.render.filepath = f"{out}/fit_{name}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/fit_study.blend")
