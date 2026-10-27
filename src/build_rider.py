import bpy, bmesh, math, sys
from mathutils import Vector
import numpy as np
OUT='/workspace/powder'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT+'/src/hunyuan_raw.glb')
ob=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
for o in list(bpy.context.scene.objects):
    if o!=ob: bpy.data.objects.remove(o)
ob.parent=None; ob.name='Rider'
bpy.context.view_layer.objects.active=ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
H=1.7
vs=np.array([v.co[:] for v in ob.data.vertices]); mn,mx=vs.min(0),vs.max(0)
s=H/(mx[2]-mn[2])
for v in ob.data.vertices:
    c=v.co; v.co=Vector(((c.x-(mn[0]+mx[0])/2)*s,(c.y-(mn[1]+mx[1])/2)*s,(c.z-mn[2])*s))
# clean + decimate
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=0.0005);bpy.ops.object.mode_set(mode='OBJECT')
tris=sum(len(p.vertices)-2 for p in ob.data.polygons)
m=ob.modifiers.new('dec','DECIMATE');m.ratio=min(1,9000/tris);bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.shade_smooth()
# vertex colors projected from reference sheet
def ld(f):
    im=bpy.data.images.load(f);w,h=im.size;a=np.array(im.pixels[:]).reshape(h,w,4)[::-1,:,:3];return a
F=ld(OUT+'/src/front.png');B=ld(OUT+'/src/back.png')
vs=np.array([v.co[:] for v in ob.data.vertices]);mn,mx=vs.min(0),vs.max(0)
FRONT=float(sys.argv[-1]) if sys.argv[-1] in('1','-1') else -1.0  # front direction along Y
def samp(img,u,v):
    h,w,_=img.shape;x=int(np.clip(u,0,.999)*w);y=int(np.clip(v,0,.999)*h)
    # small 3x3 average
    return img[max(0,y-1):y+2,max(0,x-1):x+2].reshape(-1,3).mean(0)
ca=ob.data.color_attributes.new('Col','FLOAT_COLOR','POINT')
for v in ob.data.vertices:
    u=(v.co.x-mn[0])/(mx[0]-mn[0]); t=(mx[2]-v.co.z)/(mx[2]-mn[2])
    if v.normal.y*FRONT>=-0.15:
        c=samp(F,u if FRONT<0 else 1-u,t)
    else:
        c=samp(B,1-u if FRONT<0 else u,t)
    # if sampled background grey, push toward neighbour-ish jacket color
    if abs(c[0]-c[1])<0.04 and abs(c[1]-c[2])<0.06 and c.mean()>0.7 and t>0.3: c=np.array([.93,.45,.1])
    lin=[ (x/12.92 if x<0.04045 else ((x+0.055)/1.055)**2.4) for x in c]
    ca.data[v.index].color=(*lin,1)
def vcmat(name):
    mt=bpy.data.materials.new(name);mt.use_nodes=True;nt=mt.node_tree;bs=nt.nodes['Principled BSDF']
    n=nt.nodes.new('ShaderNodeVertexColor');n.layer_name='Col';nt.links.new(n.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=0.8;return mt
ob.data.materials.append(vcmat('RiderMat'))
# snowboard along X under feet
bm=bmesh.new();L,Wd,T=1.55,0.30,0.025;N=24
pts=[]
for i in range(N+1):
    a=-math.pi/2+math.pi*i/N;pts.append(( L/2-Wd/2+math.cos(a)*Wd/2, math.sin(a)*Wd/2))
for i in range(N+1):
    a=math.pi/2+math.pi*i/N;pts.append((-L/2+Wd/2+math.cos(a)*Wd/2, math.sin(a)*Wd/2))
top=[bm.verts.new((x,y,T)) for x,y in pts];bot=[bm.verts.new((x,y,0)) for x,y in pts]
bm.faces.new(top);bm.faces.new(list(reversed(bot)))
n=len(pts)
for i in range(n):bm.faces.new((bot[i],bot[(i+1)%n],top[(i+1)%n],top[i]))
for v in top+bot:
    if abs(v.co.x)>L/2-0.12: v.co.z+= (abs(v.co.x)-(L/2-0.12))*0.5  # kick tails
bme=bpy.data.meshes.new('Board');bm.to_mesh(bme);board=bpy.data.objects.new('Board',bme);bpy.context.collection.objects.link(board)
bca=bme.color_attributes.new('Col','FLOAT_COLOR','POINT')
cream=(.85,.82,.72);teal=(.05,.32,.48);navy=(.01,.03,.12);orng=(.85,.25,.03)
for v in bme.vertices:
    x=v.co.x/L+0.5;y=v.co.y/Wd+0.5
    k=x+0.35*abs(y-0.5)
    col=cream if k<0.3 else navy if k<0.42 else orng if k<0.52 else teal if k<0.62 else cream if k<0.72 else teal
    if v.co.z<0.005: col=teal
    bca.data[v.index].color=(*col,1)
board.data.materials.append(vcmat('BoardMat'))
for p in bme.polygons:p.use_smooth=False
# shift rider so boots sit on board
ob.location.z=T
# armature
arm=bpy.data.armatures.new('RigData');rig=bpy.data.objects.new('RiderRig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
def b(name,h,t,par=None):
    e=arm.edit_bones.new(name);e.head=Vector(h);e.tail=Vector(t);e.roll=0
    if par:e.parent=arm.edit_bones[par];e.use_connect=False
    return e
z=lambda f:f*H+T
b('root',(0,0,0),(0,0.3,0))
b('board',(0,0,0.01),(0.3,0,0.01),'root')
b('hips',(0,0,z(.50)),(0,0,z(.60)),'root')
b('spine',(0,0,z(.60)),(0,0,z(.74)),'hips')
b('head',(0,0,z(.80)),(0,0,z(1.0)),'spine')
for sd,sx in(('L',1),('R',-1)):
    b('upperarm.'+sd,(sx*.12*H,0,z(.73)),(sx*.16*H,0,z(.59)),'spine')
    b('forearm.'+sd,(sx*.16*H,0,z(.59)),(sx*.18*H,0,z(.45)),'upperarm.'+sd)
    b('thigh.'+sd,(sx*.08*H,0,z(.48)),(sx*.085*H,0,z(.26)),'hips')
    b('shin.'+sd,(sx*.085*H,0,z(.26)),(sx*.09*H,0,z(.04)),'thigh.'+sd)
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.selected_objects:o.select_set(False)
ob.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_NAME')
segs=[(bn.name,bn.head_local.copy(),bn.tail_local.copy()) for bn in arm.bones if bn.name not in('root','board')]
def dseg(p,a,b):
    ab=b-a;t=max(0,min(1,(p-a).dot(ab)/ab.length_squared));return (a+ab*t-p).length
for v in ob.data.vertices:
    co=v.co+ob.location
    d=sorted((dseg(co,a,b),n) for n,a,b in segs)
    # keep arms off torso: arm bones only if vertex is lateral of shoulder line
    w=[(n,1/(dd+0.02)**4) for dd,n in d[:2]];sm=sum(x for _,x in w)
    for n,x in w: ob.vertex_groups[n].add([v.index],x/sm,'REPLACE')
print('custom weights')
board.parent=rig
vg=board.vertex_groups.new(name='board');vg.add(list(range(len(bme.vertices))),1.0,'REPLACE')
md=board.modifiers.new('arm','ARMATURE');md.object=rig
# animations
pb=rig.pose.bones
for p in pb:p.rotation_mode='XYZ'
FB=FRONT # sign of facing; bend knees toward front
def key(act,f,poses):
    for p in pb:
        r,l=poses.get(p.name,((0,0,0),(0,0,0)))
        p.rotation_euler=[math.radians(a) for a in r];p.location=l
        p.keyframe_insert('rotation_euler',frame=f);p.keyframe_insert('location',frame=f)
def make(name,frames):
    rig.animation_data_create();a=bpy.data.actions.new(name);rig.animation_data.action=a
    for f,po in frames:key(a,f,po)
    tr=rig.animation_data.nla_tracks.new();tr.name=name;tr.strips.new(name,1,a);rig.animation_data.action=None
    return a
K=FB # knee forward sign via X rotation
def crouch(d,arm_out,twist=0):
    return {'hips':((0,0,0),(0,0,0)),'root':((0,0,0),(0,0,0)),
      'thigh.L':((-K*d*55,0,0),(0,0,0)),'thigh.R':((-K*d*55,0,0),(0,0,0)),
      'shin.L':((K*d*95,0,0),(0,0,0)),'shin.R':((K*d*95,0,0),(0,0,0)),
      'spine':((-K*d*25,0,-twist),(0,0,0)),'head':((K*d*15,0,0),(0,0,0)),
      'upperarm.L':((0,0,arm_out),(0,0,0)),'upperarm.R':((0,0,-arm_out),(0,0,0)),
      'forearm.L':((-K*20,0,0),(0,0,0)),'forearm.R':((-K*20,0,0),(0,0,0))}
def drop(po,dz):
    po['hips']=(po['hips'][0],(0,dz,0));return po  # bone local Y = world Z for upward bone
make('Ride',[(1,drop(crouch(.45,35,-15),-0.17)),(13,drop(crouch(.55,40,-10),-0.22)),(25,drop(crouch(.45,35,-15),-0.17))])
g=crouch(.9,30);g=drop(g,-0.05)
g['upperarm.L']=((-K*25,0,-15),(0,0,0));g['forearm.L']=((-K*10,0,0),(0,0,0));g['spine']=((-K*45,0,0),(0,0,0))
g['board']=((0,0,0),(0,0,0))
pre=drop(crouch(.45,35,-15),-0.17)
make('Grab',[(1,pre),(8,g),(22,g),(30,pre)])
# legs tucked: lift board with hips drop compensation -> raise board bone
for f,dz in((1,0),(8,0.32),(22,0.32),(30,0)):
    rig.animation_data.action=bpy.data.actions['Grab'];pb['board'].location=(0,0,dz) ;pb['board'].keyframe_insert('location',frame=f)
rig.animation_data.action=None
for p in pb: p.rotation_euler=(0,0,0); p.location=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/rider.blend')
bpy.ops.export_scene.gltf(filepath=OUT+'/assets/rider.glb',export_format='GLB',export_animations=True,export_animation_mode='NLA_TRACKS',export_apply=False,export_vertex_color='ACTIVE')
tri=sum(len(p.vertices)-2 for o in(ob,board) for p in o.data.polygons);print('TRIS',tri)
