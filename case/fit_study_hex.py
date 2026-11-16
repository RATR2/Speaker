# Speaker case dimension-fit blockout. Units mm. X = long axis (left/right), Y = front(-)/back(+), Z up.
import bpy, bmesh, math, sys
from mathutils import Vector

# ---- parameters ----
F      = 76.0     # hex across flats (Z height), flat top
WALL   = 2.5
R      = F/math.sqrt(3)          # hex circumradius (corner at +-Y)
DRV    = 50.0; DRV_D = 25.0      # driver frame 50x50, depth guess
PR_W, PR_H, PR_T = 90.0, 50.0, 6.0   # passive radiator 90x50
PCB    = (100.0, 55.0, 1.6)
BAT    = (100.0, 60.0, 11.0)     # X,Y,Z lying flat
BOOST  = (67.0, 44.0, 16.0)      # HW-317 incl display guess
TP     = (28.0, 17.0, 5.0)
ESP    = (55.0, 28.0, 13.0)
AMP    = (17.78, 19.05, 6.0)
SW_D   = 20.0                    # round rocker, 20 mm hole
CHAMBER = DRV_D + 2*WALL + 4       # X length per driver chamber
BODY_L  = PCB[0] + 6             # electronics bay
L = max(BODY_L + 2*CHAMBER, 2*PR_W + 8) + 20   # +20: a clear slot beside the battery for the back-wall switch

def mat(name, rgba):
    m = bpy.data.materials.new(name); m.diffuse_color = rgba; return m
M = {k: mat(k, c) for k, c in dict(shell=(.6,.7,.9,.25), pcb=(.1,.5,.2,1), bat=(.8,.3,.1,1),
     boost=(.2,.3,.8,1), tp=(.7,.1,.6,1), esp=(.1,.1,.1,1), amp=(.9,.8,.1,1),
     drv=(.9,.9,.9,1), pr=(.9,.4,.4,1), sw=(.0,.8,.8,1)).items()}

def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object
    o.name = name; o.scale = size; o.data.materials.append(M[m]); return o

def cyl(name, r, d, loc, rot, m):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot); o = bpy.context.object
    o.name = name; o.data.materials.append(M[m]); return o

bpy.ops.wm.read_factory_settings(use_empty=True)
for k, c in dict(shell=(.6,.7,.9,.25), pcb=(.1,.5,.2,1), bat=(.8,.3,.1,1), boost=(.2,.3,.8,1),
    tp=(.7,.1,.6,1), esp=(.1,.1,.1,1), amp=(.9,.8,.1,1), drv=(.9,.9,.9,1), pr=(.9,.4,.4,1), sw=(0,.8,.8,1)).items():
    pass
M = {k: mat(k, c) for k, c in dict(shell=(.6,.7,.9,.25), pcb=(.1,.5,.2,1), bat=(.8,.3,.1,1),
     boost=(.2,.3,.8,1), tp=(.7,.1,.6,1), esp=(.1,.1,.1,1), amp=(.9,.8,.1,1),
     drv=(.9,.9,.9,1), pr=(.9,.4,.4,1), sw=(0,.8,.8,1)).items()}

# hex shell (flat top): cylinder with 6 verts rotated so corners sit at +-Y
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=R, depth=L)
shell = bpy.context.object
shell.rotation_euler = (0, math.radians(90), 0)
bpy.context.view_layer.update()
shell.name = "shell_hex"; shell.data.materials.append(M['shell'])
# verify flat top: max Z of verts should be F/2
zmax = max((shell.matrix_world @ v.co).z for v in shell.data.vertices)
print("hex zmax (want %.1f):" % (F/2), round(zmax, 2))

parts = []
x0 = 0
zf = -F/2 + WALL            # inner floor
# PCB on 5 mm standoffs
z_pcb = -15.0   # raised on tall standoffs so the 55 mm board clears the hex slope
parts.append(box("pcb", PCB, (0, 0, z_pcb), 'pcb'))
# ESP + amps on PCB top
parts.append(box("esp32", ESP, (-25, 0, z_pcb + PCB[2]/2 + ESP[2]/2), 'esp'))
parts.append(box("amp_U1", AMP, (22, -12, z_pcb + PCB[2]/2 + AMP[2]/2), 'amp'))
parts.append(box("amp_U2", AMP, (22, 12, z_pcb + PCB[2]/2 + AMP[2]/2), 'amp'))
# battery above PCB (lying flat), then boost beside/above
z_bat = z_pcb + PCB[2]/2 + ESP[2] + 2 + BAT[2]/2
parts.append(box("battery", BAT, (0, 0, z_bat), 'bat'))
z_boost = z_bat + BAT[2]/2 + BOOST[2]/2
parts.append(box("boost_HW317", BOOST, (0, 0, z_boost), 'boost'))
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
def on_wall(sign_z, depth_in, t=0.0):
    """point inside the back slanted wall (sign_z=+1 upper-back, -1 lower-back); depth_in measured from the OUTER face"""
    n = Vector((0, c30, sign_z*s30)); tan = Vector((0, -sign_z*s30, c30))
    return n*(F/2 - depth_in) + tan*t
# TP4056 behind the lower-back wall, USB-C end touching the wall, port through it
p_usb = on_wall(-1, WALL + 14, 0)     # TP4056 28 mm long along the wall normal
tp = box("tp4056", (TP[1], TP[0], TP[2]), (45, p_usb.y, p_usb.z), 'tp'); tp.rotation_euler = (math.radians(-30), 0, 0); parts.append(tp)
p_port = on_wall(-1, WALL/2, 0)
usb = box("usbc_port", (9, WALL+1.0, 3.5), (45, p_port.y, p_port.z), 'sw'); usb.rotation_euler = (math.radians(-30), 0, 0); parts.append(usb)
# 20 mm round rocker through the upper-back wall, body 14 mm deep behind it
p_sw = on_wall(+1, 7, 0)
sw = cyl("switch_20mm", SW_D/2, 14, (-62, p_sw.y, p_sw.z), (math.radians(-60), 0, 0), 'sw'); parts.append(sw)
print("wall check: usb centre dist from axis along normal=%.1f (outer face %.1f); switch=%.1f" %
      (Vector((0,p_port.y,p_port.z)).length, F/2, Vector((0,p_sw.y,p_sw.z)).length))
# end chambers: driver on a front dome, PR on end cap
for s, side in ((-1, "L"), (1, "R")):
    # driver on the end cap, firing +-X, under a dome bulging outward
    parts.append(box(f"driver_{side}", (DRV_D, DRV, DRV), (s*(L/2 - DRV_D/2 - WALL), 0, 0), 'drv'))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=DRV/2+8, location=(s*(L/2), 0, 0)); d = bpy.context.object
    d.name = f"dome_{side}"; d.scale = (0.4, 1, 1); d.data.materials.append(M['shell'])
    # passive radiator on the front, 90 along X, 50 tall, centred over the driver end
    parts.append(box(f"PR_{side}", (PR_W, PR_T, PR_H), (s*(PR_W/2 + 2), -R + PR_T/2 - 1, 0), 'pr'))

# ---- report: interior fit vs hex interior ----
def hex_half_width(z, rr):          # half-width in Y of flat-top hex at height z
    return rr - abs(z)/math.sqrt(3)
Ri = R - WALL/math.cos(math.radians(30))
print("Ri=%.1f  inner height=%.1f" % (Ri, F-2*WALL))
for o in parts:
    if o.name.startswith(("pcb","battery","boost","tp","esp","amp")):
        hw = o.dimensions.y/2
        zt = max(abs(o.location.z - o.dimensions.z/2), abs(o.location.z + o.dimensions.z/2))
        ok_y = hw <= hex_half_width(zt, Ri)
        ok_z = (o.location.z + o.dimensions.z/2) <= F/2 - WALL
        print(f"{o.name:12s} dims={tuple(round(v,1) for v in o.dimensions)} y_ok={ok_y} z_ok={ok_z}")
print("body L=%.0f  total (domes extra)=%.0f  H=%.0f  W(corners)=%.0f" % (L, L, F, 2*R))
sw_hits=[o.name for o in parts if o.name in ("battery","pcb","boost_HW317","esp32") and abs(o.location.x-(-62))<o.dimensions.x/2+SW_D/2]
print("switch x-overlap with:", sw_hits)
print("total with domes=%.0f (limit 240)" % (L + 2*0.4*(DRV/2+8)))
print("PR pair spans %.0f of %.0f body; electronics bay %.0f" % (2*PR_W, L, BODY_L))

# ---- render ----
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'
for o in bpy.data.objects:
    if o.name.startswith(('shell','dome')): o.display_type='WIRE'
sc.render.resolution_x, sc.render.resolution_y = 1400, 800
bpy.ops.object.light_add(type='SUN', location=(100, -100, 200)); bpy.context.object.data.energy = 4
w = bpy.data.worlds.new("w"); w.color = (.9,.9,.92); sc.world = w
out = sys.argv[sys.argv.index("--")+1]
for name, loc in (("back", (0, 330, 120)), ("iso", (210, -230, 150)), ("top", (0, 0, 380)), ("end", (330, 0, 20))):
    bpy.ops.object.camera_add(location=loc); cam = bpy.context.object
    d = Vector((0,0,0)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = 2000
    if name == "top": cam.data.type = 'ORTHO'; cam.data.ortho_scale = 260
    sc.camera = cam; sc.render.filepath = f"{out}/fit_{name}.png"
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/fit_study.blend")
