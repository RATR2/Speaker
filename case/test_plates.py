# Test prints cut from the real case geometry (case_assembly.blend): PR pin wall, lid hinge, lid snap, driver seat.
import bpy, bmesh, math, sys
from mathutils import Matrix, Vector
OUT = sys.argv[sys.argv.index("--")+1]
body = bpy.data.objects['body']; lid = bpy.data.objects['lid']
def link(o): bpy.context.collection.objects.link(o); return o
def dup(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name; return link(c)
def box(name, x0,x1,y0,y1,z0,z1):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (x1-x0, y1-y0, z1-z0); o.location = ((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); return o
def boolean(a, b, op):
    m = a.modifiers.new("b", 'BOOLEAN'); m.object = b; m.operation = op; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = a; bpy.ops.object.modifier_apply(modifier=m.name); bpy.data.objects.remove(b, do_unlink=True); return a
def apply_all(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
def slab(src, name, x0,x1,y0,y1,z0,z1):
    return boolean(dup(src, name), box("cut", x0,x1,y0,y1,z0,z1), 'INTERSECT')
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = name; return objs[0]
def orient(o, rot=None, shift=(0,0)):
    if rot: o.rotation_euler = rot
    apply_all(o)
    zmin = min(v.co.z for v in o.data.vertices); xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]
    o.location = (-(min(xs)+max(xs))/2 + shift[0], -(min(ys)+max(ys))/2 + shift[1], -zmin); apply_all(o); return o
def nonmanifold(o):
    bm = bmesh.new(); bm.from_mesh(o.data); n = sum(not e.is_manifold for e in bm.edges); bm.free(); return n
def export(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.ops.wm.stl_export(filepath=f"{OUT}/{name}.stl", export_selected_objects=True)

# 1. PR pin wall: front wall slab behind one radiator (x 0..96), outer face down, pins up
pr = slab(body, "t_pr", 0, 96, -63, -50, -29, 29)
# 2. lid hinge: back-top edge, body piece + lid piece (lid lifted 0.3 so they do not fuse), x -45..45
hb = slab(body, "t_hb", -45, 45, 35, 72, 8, 46); hl = slab(lid, "t_hl", -45, 45, 35, 72, 8, 46); hl.location.z += 0.3; apply_all(hl)
hinge = join([hb, hl], "t_hinge")
# 3. lid snap: front-wall pocket + lid tab at x = +99
sb = slab(body, "t_sb", 86, 107, -70, -44, 4, 46); sl = slab(lid, "t_sl", 86, 107, -70, -44, 4, 46); sl.location.z += 0.3; apply_all(sl)
snap = join([sb, sl], "t_snap")
# 4. speaker: driver seat tube + dome at the +x end (body + lid halves unioned), dome up
d1 = slab(body, "t_d1", 74, 125, -28.5, 28.5, -38, 38); d2 = slab(lid, "t_d2", 74, 125, -28.5, 28.5, -38, 38)
spk = boolean(d1, d2, 'UNION')

orient(pr, rot=(math.radians(90), 0, 0)); orient(hinge); orient(snap); orient(spk, rot=(0, math.radians(-90), 0))
for o in (pr, hinge, snap, spk):
    print(o.name, "non-manifold:", nonmanifold(o), "size", tuple(round(d,1) for d in o.dimensions))
# individual files (each centred on the origin), then one combined plate layout
names = {"test_pr_pins": pr, "test_lid_hinge": hinge, "test_lid_snap": snap, "test_speaker_seat": spk}
for n, o in names.items(): export([o], n)
pr.location += Vector((-70, 80, 0)); hinge.location += Vector((60, 80, 0)); snap.location += Vector((60, 20, 0)); spk.location += Vector((-70, -40, 0))
export([pr, hinge, snap, spk], "test_plate_all")
