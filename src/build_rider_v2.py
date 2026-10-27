import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler
OUT='/workspace/powder'; H=1.7; T=0.025
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT+'/src/hunyuan_raw.glb')
ob=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
for o in list(bpy.context.scene.objects):
    if o!=ob: bpy.data.objects.remove(o)
ob.parent=None; ob.name='Rider'; bpy.context.view_layer.objects.active=ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
xs=[v.co for v in ob.data.vertices]
mn=Vector([min(c[i] for c in xs) for i in range(3)]);mx=Vector([max(c[i] for c in xs) for i in range(3)])
s=H/(mx.z-mn.z)
for v in ob.data.vertices:
    c=v.co; v.co=Vector(((c.x-(mn.x+mx.x)/2)*s,(c.y-(mn.y+mx.y)/2)*s,(c.z-mn.z)*s+T))
# --- clean: voxel remesh -> manifold, then decimate
m=ob.modifiers.new('rm','REMESH');m.mode='VOXEL';m.voxel_size=0.014;bpy.ops.object.modifier_apply(modifier='rm')
m=ob.modifiers.new('sm','SMOOTH');m.iterations=3;m.factor=0.5;bpy.ops.object.modifier_apply(modifier='sm')
tris=sum(len(p.vertices)-2 for p in ob.data.polygons)
print('PRE TRIS',tris)
bpy.ops.object.shade_smooth()
# --- region materials (crisp per-face)
def srgb(h):
    c=[int(h[i:i+2],16)/255 for i in(0,2,4)];return [(x/12.92 if x<0.04045 else ((x+0.055)/1.055)**2.4) for x in c]+[1]
PAL={'jacket':'F07A1E','teal':'2E86A6','navy':'14234D','cream':'EFE9DC','glove':'2B7593','lens':'3FA7C9','sole':'F4F1EA','strap':'1B2C5C'}
mats={}
for n,hx in PAL.items():
    mt=bpy.data.materials.new(n);mt.use_nodes=True;bs=mt.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=srgb(hx);bs.inputs['Roughness'].default_value=0.25 if n=='lens' else 0.85
    if n=='lens':bs.inputs['Metallic'].default_value=0.3
    mt.diffuse_color=srgb(hx);ob.data.materials.append(mt);mats[n]=len(mats)
def region(c,nrm):
    t=(c.z-T)/H; ax=abs(c.x)/H; x=c.x/H; front=nrm.y<-0.25; back=nrm.y>0.3
    if t<0.035: return 'sole'
    if t<0.11: return 'teal'
    if t<0.345: return 'navy'
    if t<0.47 and ax>0.185: return 'glove'
    if t<0.80:
        if front and 0.40<t<0.51 and 0.055<ax<0.15: return 'teal'
        if front and 0.625<t<0.675 and 0.03<x<0.095: return 'teal'
        if front and 0.45<t<0.74 and -0.035<x<-0.02: return 'teal'
        if 0.62<t<0.69 and 0.165<x and not back: return 'teal'
        if back and 0.655<t<0.685 and ax<0.13: return 'teal'
        return 'jacket'
    if t<0.885:
        if front and ax<0.075: return 'navy'
        return 'jacket' if t<0.85 or not back else 'cream'
    if t<0.965 and front and ax<0.105:
        return 'cream' if ax>0.088 or t>0.955 or t<0.893 else 'lens'
    if back and 0.89<t<0.93: return 'strap'
    return 'cream'
for p in ob.data.polygons: p.material_index=mats[region(p.center,p.normal)]
# --- board
bm=bmesh.new();L,Wd,BT=1.55,0.30,0.025;N=24;pts=[]
for i in range(N+1):
    a=-math.pi/2+math.pi*i/N;pts.append(( L/2-Wd/2+math.cos(a)*Wd/2, math.sin(a)*Wd/2))
for i in range(N+1):
    a=math.pi/2+math.pi*i/N;pts.append((-L/2+Wd/2+math.cos(a)*Wd/2, math.sin(a)*Wd/2))
top=[bm.verts.new((x,y,BT)) for x,y in pts];bot=[bm.verts.new((x,y,0)) for x,y in pts]
ft=bm.faces.new(top);fb=bm.faces.new(list(reversed(bot)));n=len(pts)
side=[bm.faces.new((bot[i],bot[(i+1)%n],top[(i+1)%n],top[i])) for i in range(n)]
for v in top+bot:
    if abs(v.co.x)>L/2-0.12: v.co.z+=(abs(v.co.x)-(L/2-0.12))*0.5
# graphic: cut top face with chevron-ish bands via bisect along x planes (tilted)
geom=bm.verts[:]+bm.edges[:]+bm.faces[:]
for k in(-0.22,-0.08,0.02,0.12,0.25):
    r=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(k*L,0,0),plane_no=(1,0.45,0))
bme=bpy.data.meshes.new('Board');bm.to_mesh(bme);board=bpy.data.objects.new('Board',bme);bpy.context.collection.objects.link(board)
for nme in('cream','navy','jacket','teal'):board.data.materials.append(bpy.data.materials[nme])
for p in bme.polygons:
    c=p.center;k=(c.x+0.45*c.y)/L
    i=0 if k<-0.22 else 1 if k<-0.08 else 2 if k<0.02 else 1 if k<0.12 else 3 if k<0.25 else 0
    if k>0.32: i=3
    if p.normal.z<-0.5: i=3
    p.material_index=i
# --- armature
arm=bpy.data.armatures.new('RigData');rig=bpy.data.objects.new('RiderRig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
z=lambda f:f*H+T
def b(name,h,t,par=None,deform=True):
    e=arm.edit_bones.new(name);e.head=Vector(h);e.tail=Vector(t);e.roll=0;e.use_deform=deform
    if par:e.parent=arm.edit_bones[par]
    return e
b('root',(0,0,0),(0,0.3,0),deform=False)
b('board',(0,0,0.0),(0.3,0,0.0),'root')
b('hips',(0,0,z(.50)),(0,0,z(.60)),'root')
b('spine',(0,0,z(.60)),(0,0,z(.70)),'hips')
b('chest',(0,0,z(.70)),(0,0,z(.79)),'spine')
b('head',(0,0,z(.80)),(0,0,z(1.0)),'chest')
for sd,sx in(('L',1),('R',-1)):
    b('upperarm.'+sd,(sx*.12*H,0,z(.73)),(sx*.16*H,0.0,z(.59)),'chest')
    b('forearm.'+sd,(sx*.16*H,0.0,z(.59)),(sx*.185*H,-0.02,z(.45)),'upperarm.'+sd).use_connect=True
    b('thigh.'+sd,(sx*.08*H,0,z(.48)),(sx*.085*H,-0.03,z(.26)),'hips')
    b('shin.'+sd,(sx*.085*H,-0.03,z(.26)),(sx*.09*H,0,z(.05)),'thigh.'+sd).use_connect=True
    b('ik.'+sd,(sx*.09*H,0,z(.05)),(sx*.09*H,0.15,z(.05)),'board',False)
    b('pole.'+sd,(sx*.085*H,-0.8,z(.26)),(sx*.085*H,-0.9,z(.26)),'root',False)
bpy.ops.object.mode_set(mode='OBJECT')
# --- skinning: heat weights
for o in bpy.context.selected_objects:o.select_set(False)
ob.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
unw=sum(1 for v in ob.data.vertices if not any(g.weight>0.01 for g in v.groups))
print('UNWEIGHTED',unw,len(ob.data.vertices))
if unw>len(ob.data.vertices)*0.02:
    # fallback: smooth distance falloff, normalized
    for vg in list(ob.vertex_groups):ob.vertex_groups.remove(vg)
    ob.parent=None;ob.select_set(True);rig.select_set(True);bpy.ops.object.parent_set(type='ARMATURE_NAME')
    segs=[(bn.name,bn.head_local.copy(),bn.tail_local.copy()) for bn in arm.bones if bn.use_deform and bn.name!='board']
    def dseg(p,a,bb):
        ab=bb-a;t=max(0,min(1,(p-a).dot(ab)/ab.length_squared));return (a+ab*t-p).length
    for v in ob.data.vertices:
        d=sorted((dseg(v.co,a,bb),nm) for nm,a,bb in segs)[:3]
        w=[(nm,math.exp(-((dd-d[0][0])/0.04)**2)) for dd,nm in d];sm=sum(x for _,x in w)
        for nm,x in w: ob.vertex_groups[nm].add([v.index],x/sm,'REPLACE')
    print('FALLBACK weights')
bpy.context.view_layer.objects.active=ob
m=ob.modifiers.new('dec','DECIMATE');m.ratio=8600/tris
bpy.ops.object.modifier_move_to_index(modifier='dec',index=0);bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=0.0001);bpy.ops.mesh.delete_loose();bpy.ops.object.mode_set(mode='OBJECT')
# keep feet off board group; smooth + normalize
bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_smooth(group_select_mode='ALL',factor=0.5,repeat=3)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
# board as child of bone 'board'
board.parent=rig;board.parent_type='BONE';board.parent_bone='board'
bpy.context.view_layer.update();board.matrix_world=Matrix.Identity(4)
# --- IK
pb=rig.pose.bones
for sd in 'LR':
    c=pb['shin.'+sd].constraints.new('IK');c.target=rig;c.subtarget='ik.'+sd;c.pole_target=rig;c.pole_subtarget='pole.'+sd;c.pole_angle=math.radians(-90);c.chain_count=2
for p in pb:p.rotation_mode='XYZ'
# --- animations
FPS=24;bpy.context.scene.render.fps=FPS
def R(*a):return [math.radians(x) for x in a]
BASE={'hips':dict(location=(0,-0.16,0)),'spine':dict(rotation_euler=R(18,0,0)),'chest':dict(rotation_euler=R(8,0,-10)),'head':dict(rotation_euler=R(-20,0,15)),
 'upperarm.L':dict(rotation_euler=R(-10,0,-35)),'upperarm.R':dict(rotation_euler=R(-10,0,35)),'forearm.L':dict(rotation_euler=R(-25,0,0)),'forearm.R':dict(rotation_euler=R(-25,0,0))}
def pose(over=None):
    d={k:dict(v) for k,v in BASE.items()}
    for k,v in (over or {}).items(): d.setdefault(k,{}).update(v)
    return d
def setkey(f,po):
    for p in pb:
        if p.name.startswith(('ik.','pole.')):continue
        d=po.get(p.name,{})
        p.location=d.get('location',(0,0,0));p.rotation_euler=d.get('rotation_euler',(0,0,0))
        p.keyframe_insert('location',frame=f);p.keyframe_insert('rotation_euler',frame=f)
def make(name,keys,loop=False):
    rig.animation_data_create();a=bpy.data.actions.new(name);rig.animation_data.action=a
    for f,po in keys:setkey(f,po)
    tr=rig.animation_data.nla_tracks.new();tr.name=name;st=tr.strips.new(name,1,a);tr.mute=True
    rig.animation_data.action=None;return a
def rootpivot(rot,c=Vector((0,0,0.85))):
    M=Euler(rot).to_matrix();loc=c-M@c;return dict(rotation_euler=rot,location=tuple(loc))
make('Ride',[(1,pose()),(13,pose({'hips':dict(location=(0,-0.22,0)),'spine':dict(rotation_euler=R(24,0,0))})),(25,pose())])
make('TurnL',[(1,pose({'root':dict(rotation_euler=R(-14,0,0)),'hips':dict(location=(0,-0.2,0)),'spine':dict(rotation_euler=R(28,0,0)),'upperarm.R':dict(rotation_euler=R(-40,0,55))})),
              (13,pose({'root':dict(rotation_euler=R(-16,0,0)),'hips':dict(location=(0,-0.24,0)),'spine':dict(rotation_euler=R(30,0,0)),'upperarm.R':dict(rotation_euler=R(-45,0,60))})),
              (25,pose({'root':dict(rotation_euler=R(-14,0,0)),'hips':dict(location=(0,-0.2,0)),'spine':dict(rotation_euler=R(28,0,0)),'upperarm.R':dict(rotation_euler=R(-40,0,55))}))])
make('TurnR',[(1,pose({'root':dict(rotation_euler=R(14,0,0)),'hips':dict(location=(0,-0.2,0)),'spine':dict(rotation_euler=R(-2,0,0)),'upperarm.L':dict(rotation_euler=R(30,0,-55))})),
              (13,pose({'root':dict(rotation_euler=R(16,0,0)),'hips':dict(location=(0,-0.24,0)),'spine':dict(rotation_euler=R(-4,0,0)),'upperarm.L':dict(rotation_euler=R(35,0,-60))})),
              (25,pose({'root':dict(rotation_euler=R(14,0,0)),'hips':dict(location=(0,-0.2,0)),'spine':dict(rotation_euler=R(-2,0,0)),'upperarm.L':dict(rotation_euler=R(30,0,-55))}))])
tuck=lambda extra={}:pose({'board':dict(location=(0,0,0.34)),'hips':dict(location=(0,-0.02,0)),'spine':dict(rotation_euler=R(35,0,0)),**extra})
make('Grab',[(1,pose()),(5,tuck()),(8,tuck({'upperarm.L':dict(rotation_euler=R(-35,0,-10)),'forearm.L':dict(rotation_euler=R(-15,0,0))})),
             (14,tuck({'upperarm.L':dict(rotation_euler=R(-40,0,-5)),'forearm.L':dict(rotation_euler=R(-10,0,0)),'upperarm.R':dict(rotation_euler=R(-20,0,80)),'head':dict(rotation_euler=R(-10,0,25))})),
             (20,tuck({'upperarm.L':dict(rotation_euler=R(-35,0,-10)),'forearm.L':dict(rotation_euler=R(-15,0,0))})),(24,pose())])
sp=[];NS=14
for i in range(NS+1):
    a=360*i/NS;e=tuck({'upperarm.L':dict(rotation_euler=R(-20,0,-70)),'upperarm.R':dict(rotation_euler=R(-20,0,70))}) if 0<i<NS else pose()
    e['root']=dict(rotation_euler=R(0,0,a));sp.append((1+i,e))
make('Spin360',sp)
fl=[];NF=17
for i in range(NF+1):
    a=-360*i/NF;e=tuck({'upperarm.L':dict(rotation_euler=R(-50,0,-20)),'upperarm.R':dict(rotation_euler=R(-50,0,20)),'spine':dict(rotation_euler=R(50,0,0))}) if 0<i<NF else pose()
    e['root']=rootpivot(R(a,0,0));fl.append((1+i,e))
make('Flip',fl)
make('Land',[(1,pose({'board':dict(location=(0,0,0.1))})),(4,pose({'hips':dict(location=(0,-0.34,0)),'spine':dict(rotation_euler=R(40,0,0)),'upperarm.L':dict(rotation_euler=R(-30,0,-60)),'upperarm.R':dict(rotation_euler=R(-30,0,60))})),(12,pose())])
make('Crash',[(1,pose()),(6,pose({'root':rootpivot(R(25,0,20)),'upperarm.L':dict(rotation_euler=R(-120,0,-60)),'upperarm.R':dict(rotation_euler=R(-120,0,60)),'spine':dict(rotation_euler=R(-25,0,0))})),
              (14,pose({'root':rootpivot(R(80,0,40),Vector((0,0,0.3))),'hips':dict(location=(0,-0.25,0)),'upperarm.L':dict(rotation_euler=R(-150,0,-30)),'upperarm.R':dict(rotation_euler=R(-60,0,70)),'head':dict(rotation_euler=R(30,0,0))})),
              (22,pose({'root':rootpivot(R(85,0,45),Vector((0,0,0.3))),'hips':dict(location=(0,-0.3,0)),'upperarm.L':dict(rotation_euler=R(-100,0,-80)),'upperarm.R':dict(rotation_euler=R(-40,0,80)),'head':dict(rotation_euler=R(20,0,0))})),
              (36,pose())])
for p in pb:p.location=(0,0,0);p.rotation_euler=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/rider.blend')
for o in bpy.context.selected_objects:o.select_set(False)
for o in(ob,board,rig):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'/assets/rider.glb',export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_def_bones=True,export_bake_animation=False)
print('TRIS',sum(len(p.vertices)-2 for o in(ob,board) for p in o.data.polygons))
