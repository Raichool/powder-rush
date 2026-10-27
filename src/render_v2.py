import bpy,math,sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/workspace/powder/rider.blend')
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.device='CPU'
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.75,.8,.88,1)
l=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN'));l.data.energy=3;l.rotation_euler=(math.radians(40),0,math.radians(-30));sc.collection.objects.link(l)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam
rig=bpy.data.objects['RiderRig']
def shoot(path,ang,d=4.2,tz=0.85,cz=1.0):
    a=math.radians(ang);cam.location=(math.sin(a)*d,-math.cos(a)*d,cz)
    cam.rotation_euler=(Vector((0,0,tz))-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=path;bpy.ops.render.render(write_still=True)
mode=sys.argv[-1]
if mode=='rest':
    sc.render.resolution_x=600;sc.render.resolution_y=800
    for n,a in(('front',0),('back',180),('34',35)):shoot(f'/workspace/rider_v2_{n}.png',a)
else:
    sc.render.resolution_x=300;sc.render.resolution_y=360
    for spec in mode.split(','):
        act,f=spec.split(':');rig.animation_data.action=bpy.data.actions[act];sc.frame_set(int(f))
        shoot(f'/workspace/powder/src/_p_{act}_{f}.png',35,d=5.2,tz=0.9,cz=1.4)
