# Colored showcase model + renders for the speaker case. Run from case_assembly.blend:
#   blender -b print/case_assembly.blend --python showcase.py -- <outdir> [stills|video]
import bpy, math, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--")+1]; MODE = sys.argv[sys.argv.index("--")+2] if len(sys.argv) > sys.argv.index("--")+2 else "stills"
FLAT = 51.0; W = FLAT*(1+math.sqrt(2)); L = 216.0; WALL = 2.5
ZB, ZT = -(W/2-WALL), (W/2-WALL); ZC = FLAT/2
HAX_Y, HAX_Z = W/2+5.0, ZC+2.5
body = bpy.data.objects['body']; lid = bpy.data.objects['lid']

def mat(name, rgb, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1); return m
M = dict(body=mat("body",(0.10,0.20,0.38),0.35), lid=mat("lid",(0.12,0.55,0.62),0.30), pcb=mat("pcb",(0.02,0.30,0.12),0.4),
         black=mat("black",(0.02,0.02,0.02),0.5), silver=mat("silver",(0.75,0.76,0.80),0.25,1.0), amp=mat("amp",(0.30,0.05,0.45),0.4),
         bat=mat("bat",(0.10,0.30,0.85),0.35,0.0), batlabel=mat("batlabel",(0.95,0.95,0.95),0.5), boost=mat("boost",(0.05,0.15,0.75),0.4),
         tp=mat("tp",(0.05,0.12,0.55),0.4), pr=mat("pr",(0.92,0.92,0.90),0.4), driver=mat("driver",(0.04,0.04,0.05),0.6),
         rocker=mat("rocker",(0.85,0.08,0.08),0.4), cable=mat("cable",(0.85,0.05,0.05),0.5), gold=mat("gold",(0.9,0.7,0.2),0.3,1.0))
body.data.materials.clear(); body.data.materials.append(M['body']); lid.data.materials.clear(); lid.data.materials.append(M['lid'])
for o in (body, lid):
    for p in o.data.polygons: p.use_smooth = False

def link(o): bpy.context.collection.objects.link(o); return o
def cube(name, cx,cy,cz, sx,sy,sz, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx,cy,cz)); o = bpy.context.object; o.name = name; o.scale = (sx,sy,sz); o.data.materials.append(M[m]); return o
def cyl(name, axis, r, depth, loc, m, seg=48):
    rot = {'x':(0,math.radians(90),0), 'y':(math.radians(90),0,0), 'z':(0,0,0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=depth, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.data.materials.append(M[m]); return o
fixed, lidparts = [], []

# ---- electronics (positions from build_case.py) ----
BOOST_TOP = ZB + 5.0 + 16.0; PCB_BOT = BOOST_TOP + 3.0; PCB_TOP = PCB_BOT + 1.6
fixed.append(cube("boost_pcb", 0,0, ZB+5.0+0.8, 67.2,43.8,1.6, 'boost'))
fixed.append(cube("boost_display", 0,-6, ZB+5.0+1.6+6, 30,18,12, 'black'))
fixed.append(cube("boost_coil", 20,10, ZB+5.0+1.6+5, 18,14,10, 'silver'))
fixed.append(cube("pcb", 0,0, PCB_BOT+0.8, 100,55,1.6, 'pcb'))
fixed.append(cube("esp32", -25,0, PCB_TOP+6.5, 55,28,13, 'black')); fixed.append(cube("esp_shield", -22,0, PCB_TOP+13.4, 24,18,1.6, 'silver'))
for i, y in enumerate((-12, 12)): fixed.append(cube(f"amp{i}", 22,y, PCB_TOP+3, 17.78,19.05,6, 'amp'))
fixed.append(cyl("cap1000uF", 'z', 5, 12, (36,-20,PCB_TOP+6), 'silver'))
# TP4056 on its platform + USB-C
TP_BOT = -18.0 - 2.5; Y_WIN = W/2 - WALL
fixed.append(cube("tp4056", 64, Y_WIN-14, TP_BOT+0.8, 17,28,1.6, 'tp')); fixed.append(cube("tp_usb", 64, Y_WIN-3.5, TP_BOT+1.6+1.65, 9,7.5,3.3, 'silver'))
# switch (20 mm round rocker) through the back wall
fixed.append(cyl("sw_body", 'y', 9.8, 14, (-68, Y_WIN-5, 0), 'black')); fixed.append(cyl("sw_rocker", 'y', 10.0, 3.2, (-68, W/2+0.6, 0), 'rocker'))
# drivers (50 x 50 x 30) in the seats, cone facing out
for s in (-1, 1):
    cx = s*(L/2 - WALL - 15)
    fixed.append(cube(f"driver{s}", cx,0,0, 30,50,50, 'driver'))
    fixed.append(cyl(f"cone{s}", 'x', 21, 6, (s*(L/2-WALL+1.5),0,0), 'silver'))
    fixed.append(cyl(f"dust{s}", 'x', 8, 7, (s*(L/2-WALL+2.5),0,0), 'black'))
# passive radiator plates (90 x 50 x 1) behind the square openings
for s in (-1, 1):
    fixed.append(cube(f"pr{s}", s*47, -(W/2-WALL)-0.6, 0, 90,1,50, 'pr'))
# battery + cradle shadow live on the lid
BAT_TOP = ZT - 9.5
lidparts.append(cube("battery", 0,0, BAT_TOP-5.5, 100,60,11, 'bat')); lidparts.append(cube("battery_label", 0,0, BAT_TOP-11-0.05, 70,40,0.3, 'batlabel'))
lidparts.append(cube("bat_plug", -2.25,-22.5, BAT_TOP-11-2, 8,5,4, 'gold'))

# ---- cable (bezier) from PCB JST to battery plug, rebuilt per lid pose ----
def make_cable(lid_matrix):
    for o in [o for o in bpy.data.objects if o.name.startswith("cable")]: bpy.data.objects.remove(o, do_unlink=True)
    p0 = Vector((-2.25,-22.5, PCB_TOP+3)); p3 = lid_matrix @ Vector((-2.25,-22.5, BAT_TOP-11-4))
    cu = bpy.data.curves.new("cable", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.2; cu.bevel_resolution = 4
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    a, b = sp.bezier_points; a.co = p0; b.co = p3
    a.handle_left = p0 + Vector((0,0,-8)); a.handle_right = p0 + Vector((0,0,25)); b.handle_left = p3 + (p0-p3)*0.35 + Vector((0,0,-10)); b.handle_right = p3 + Vector((0,0,8))
    o = link(bpy.data.objects.new("cable", cu)); o.data.materials.append(M['cable']); return o

# ---- scene, light, camera ----
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1600, 900
try: sc.eevee.taa_render_samples = 48
except Exception: pass
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new("w"); w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.55,0.62,0.75,1); bg.inputs[1].default_value = 0.6; sc.world = w
bpy.ops.mesh.primitive_plane_add(size=1200, location=(0,0,-H_FLOOR if (H_FLOOR:=W/2+3.5) else 0)); fl = bpy.context.object; fl.data.materials.append(mat("floor",(0.16,0.17,0.2),0.7))
bpy.ops.object.light_add(type='SUN', location=(200,-300,400)); sun = bpy.context.object; sun.data.energy = 1.6; sun.rotation_euler = (math.radians(50),0,math.radians(30))
bpy.ops.object.light_add(type='AREA', location=(-250,-250,200)); fill = bpy.context.object; fill.data.energy = 9000; fill.data.size = 300; fill.rotation_euler = (math.radians(60),0,math.radians(-45))
def cam_at(loc, target):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.data.lens = 45; c.data.clip_end = 5000
    c.rotation_euler = (Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler(); sc.camera = c; return c
def pose_lid(deg):
    ax = Vector((0,HAX_Y,HAX_Z)); m = Matrix.Translation(ax) @ Matrix.Rotation(math.radians(deg),4,'X') @ Matrix.Translation(-ax)
    lid.matrix_world = m
    for p in lidparts: p.matrix_world = m @ Matrix.Translation(p.location) if False else m @ Matrix.Translation(Vector(p.location))
    return m
# lidparts were created with location only; keep a copy of rest locations
rest = {p.name: p.location.copy() for p in lidparts}
def pose(deg):
    ax = Vector((0,HAX_Y,HAX_Z)); m = Matrix.Translation(ax) @ Matrix.Rotation(math.radians(deg),4,'X') @ Matrix.Translation(-ax)
    lid.matrix_world = m
    for p in lidparts: p.matrix_world = m @ Matrix.Translation(rest[p.name]) @ Matrix.Diagonal(Vector((p.scale.x,p.scale.y,p.scale.z,1)))
    make_cable(m); bpy.context.view_layer.update()
    b = bpy.data.objects['battery']; print('battery world centre', tuple(round(v,1) for v in b.matrix_world.translation), 'dims', tuple(round(v,1) for v in b.dimensions), 'vis', b.hide_render)
    return m
def still(name, deg, loc, target):
    pose(deg); cam_at(loc, target); sc.render.filepath = f"{OUT}/{name}.png"; bpy.ops.render.render(write_still=True)

if MODE == "stills":
    still("showcase_closed_front", 0, (330,-420,230), (0,0,0))
    still("showcase_closed_back", 0, (-300,430,240), (0,0,0))
    still("showcase_open", -105, (290,-420,330), (0,10,25))
    still("showcase_top_down", -135, (120,-250,470), (0,0,-10))
    # GLB models (closed + open)
    for nm, deg in (("speaker_closed", 0), ("speaker_open", -105)):
        pose(deg)
        for o in bpy.data.objects: o.select_set(o.type in ('MESH','CURVE') and o.name != fl.name)
        bpy.ops.export_scene.gltf(filepath=f"{OUT}/{nm}.glb", export_format='GLB', use_selection=True, export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/speaker_showcase.blend")
elif MODE == "video":
    # turntable: lid open, camera orbits
    pose(-105); c = cam_at((0,-450,260), (0,10,25)); pivot = bpy.data.objects.new("pivot", None); link(pivot); c.parent = pivot
    sc.frame_start, sc.frame_end = 1, 96
    pivot.rotation_euler = (0,0,0); pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0,0,math.radians(360)); pivot.keyframe_insert("rotation_euler", frame=97)
    for fc in pivot.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.image_settings.media_type = 'VIDEO'; sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.filepath = f"{OUT}/speaker_turntable.mp4"; bpy.ops.render.render(animation=True)

else:
    # ---- full animation: orbit, stop at the front, lid opens, orbit again ----
    FPS = 24; sc.render.fps = FPS
    T_ORBIT1 = (1, 120); T_OPEN = (132, 180); T_ORBIT2 = (192, 312); T_END = 324
    ax = Vector((0, HAX_Y, HAX_Z))
    hinge = link(bpy.data.objects.new("hinge", None)); hinge.location = ax; bpy.context.view_layer.update()
    for o in [lid] + lidparts:
        o.parent = hinge; o.matrix_parent_inverse = hinge.matrix_world.inverted()
    cable = make_cable(Matrix.Identity(4)); P0 = Vector((-2.25, -22.5, PCB_TOP + 3)); PLUG = Vector((-2.25, -22.5, BAT_TOP - 11 - 4))
    def cable_pose(angle):
        """curve end that follows the lid; handles give it a slack droop"""
        rot = Matrix.Rotation(angle, 3, 'X'); p3 = ax + rot @ (PLUG - ax)
        d = (p3 - P0).length
        return p3, p3 + (P0 - p3)*0.35 + Vector((0, 0, -min(14.0, 0.15*d))), p3 + rot @ Vector((0, 0, 8)), P0 + Vector((0, 0, min(30.0, 0.35*d)))
    # camera on a pivot, always looking at the middle of the speaker
    target = link(bpy.data.objects.new("look_at", None)); target.location = (0, 0, 8)
    pivot = link(bpy.data.objects.new("pivot", None))
    c = cam_at((0, -540, 400), (0, 0, 8)); c.parent = pivot
    tt = c.constraints.new('TRACK_TO'); tt.target = target; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
    def key(obj, path, idx, frame, value):
        getattr(obj, path)[idx] = value; obj.keyframe_insert(path, index=idx, frame=frame)
    key(pivot, "rotation_euler", 2, T_ORBIT1[0], 0.0); key(pivot, "rotation_euler", 2, T_ORBIT1[1], 2*math.pi)
    key(pivot, "rotation_euler", 2, T_ORBIT2[0], 2*math.pi); key(pivot, "rotation_euler", 2, T_ORBIT2[1], 4*math.pi)
    key(hinge, "rotation_euler", 0, T_OPEN[0], 0.0); key(hinge, "rotation_euler", 0, T_OPEN[1], math.radians(-110))
    key(hinge, "rotation_euler", 0, 1, 0.0); key(hinge, "rotation_euler", 0, T_END, math.radians(-110))
    for ob in (pivot, hinge):
        for fc in ob.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    # bake the cable end per frame from the hinge fcurve (handlers do not re-evaluate curves in background renders)
    hfc = [fc for fc in hinge.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if fc.array_index == 0][0]
    pts = cable.data.splines[0].bezier_points; a0, b1 = pts[0], pts[1]
    for f in range(1, T_END + 1):
        p3, hl, hr, a_hr = cable_pose(hfc.evaluate(f))
        b1.co = p3; b1.handle_left = hl; b1.handle_right = hr; a0.handle_right = a_hr
        for bp, props in ((b1, ("co", "handle_left", "handle_right")), (a0, ("handle_right",))):
            for pr in props: bp.keyframe_insert(pr, frame=f)
    for fc in cable.data.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    sc.frame_start, sc.frame_end = 1, T_END
    sc.render.resolution_x, sc.render.resolution_y = (1920, 1080)
    sc.render.image_settings.media_type = 'VIDEO'; sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.filepath = f"{OUT}/speaker_showcase_animation.mp4"
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/speaker_showcase_animation.blend")
    bpy.ops.render.render(animation=True)
