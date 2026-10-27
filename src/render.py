import bpy,math,sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/workspace/powder/rider.blend')
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.device='CPU'
sc.render.resolution_x=600;sc.render.resolution_y=800;sc.render.film_transparent=False
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.75,.8,.88,1);w.node_tree.nodes['Background'].inputs[1].default_value=1.0
l=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN'));l.data.energy=3;l.rotation_euler=(math.radians(40),0,math.radians(-30));sc.collection.objects.link(l)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam
rig=bpy.data.objects['RiderRig']
mode=sys.argv[-1]
for t in rig.animation_data.nla_tracks: t.mute=True
for p in rig.pose.bones: p.rotation_euler=(0,0,0); p.location=(0,0,0)
if mode!='rest':
    rig.animation_data.action=bpy.data.actions[mode.split(':')[0]];sc.frame_set(int(mode.split(':')[1]))
for name,ang in [('front',0),('back',180),('34',35)] if mode=='rest' else [('34',35),('side',90)]:
    if mode=='rest':pass
    a=math.radians(ang);d=4.2;cam.location=(math.sin(a)*d,-math.cos(a)*d,1.0);
    dirv=Vector((0,0,0.85))-cam.location;cam.rotation_euler=dirv.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'/workspace/rider_{name}.png' if mode=='rest' else f'/workspace/rider_pose_{mode.replace(":","_")}_{name}.png'
    bpy.ops.render.render(write_still=True)
