# Snap-pin fit coupon for the 2.7 mm PCB holes (Speaker4.kicad_pcb: 4 holes, 92 x 47 mm, board 1.6 mm thick).
# Row 1 (y=0): 2.7 mm PCB holes. Row 2 (y=14): 3.0 mm HW-317 holes, shanks 2.6/2.7/2.8/2.9.
# Four posts, shank diameters 2.3 / 2.4 / 2.5 / 2.6 (left to right) with a barbed, split pin; print upright in PETG.
import bpy, bmesh, math, sys
from mathutils import Vector
PCB_T = 1.6; HOLE = 2.7
SLOT = 0.8; SLOT_DEPTH = 5.0
def pin(name, shank_d, x, y, post_d=7.0, post_h=6.0, board_t=PCB_T):
    rs = shank_d/2; rb = rs + 0.35; z_led = board_t + 0.15; z_tip = z_led + 3.0; rt = 0.9
    prof = [(0,0),(post_d/2,0),(post_d/2,post_h),(rs,post_h),(rs,post_h+z_led),(rb,post_h+z_led),(rt,post_h+z_tip),(0,post_h+z_tip)]
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((r,0,z)) for r,z in prof]
    es = [bm.edges.new((vs[i], vs[i+1])) for i in range(len(vs)-1)]
    bmesh.ops.spin(bm, geom=vs+es, cent=(0,0,0), axis=(0,0,1), angle=2*math.pi, steps=48)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.location = (x, y, 0)
    bpy.context.view_layer.objects.active = o
    cut = bpy.data.objects.new("slot", bpy.data.meshes.new("slot")); bpy.context.collection.objects.link(cut)
    b2 = bmesh.new(); bmesh.ops.create_cube(b2, size=1.0); b2.to_mesh(cut.data); b2.free()
    cut.scale = (SLOT, 6.0, SLOT_DEPTH*2); cut.location = (x, y, post_h + 0.3 + SLOT_DEPTH)   # slot cut from tip down to 1 mm above shoulder
    cut.scale = (SLOT, 6.0, SLOT_DEPTH*2)
    m = o.modifiers.new("slot", 'BOOLEAN'); m.object = cut; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="slot"); bpy.data.objects.remove(cut)
    return o
bpy.ops.wm.read_factory_settings(use_empty=True)
base = bpy.data.objects.new("base", bpy.data.meshes.new("base")); bpy.context.collection.objects.link(base)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(base.data); bm.free()
base.scale = (48, 28, 2.0); base.location = (0, 0, -1.0)
objs = [base] + [pin(f"pin_{d}", d, -16.5 + 11*i, 0) for i, d in enumerate((2.3, 2.4, 2.5, 2.6))] + [pin(f"pin3_{d}", d, -16.5 + 11*i, 14, post_d=6.0, post_h=5.0) for i, d in enumerate((2.6, 2.7, 2.8, 2.9))]
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = base; bpy.ops.object.join()
j = bpy.context.object; j.name = "snap_pin_coupon"
bm = bmesh.new(); bm.from_mesh(j.data); print("non-manifold edges:", sum(not e.is_manifold for e in bm.edges)); bm.free()
bpy.ops.wm.stl_export(filepath=sys.argv[sys.argv.index("--")+1] + "/snap_pin_coupon.stl", export_selected_objects=True)
