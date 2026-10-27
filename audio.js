// Powder Rush audio — 100% procedural Web Audio (no samples, no third-party assets). Code: original, same license as the game.
(()=>{
let gr=0,grG,grF,ctx,M,SFX,MUS,noise,slide,slideF,slideG,wind,windF,windG,whG,whF,muted=localStorage.getItem('pr_mute')==='1',I=0,step=0,nextT=0,timer,rec;
const BPM=140,S16=60/BPM/4;
function mkNoise(){const b=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate),d=b.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;return b;}
function loopNoise(type,f,q){const s=ctx.createBufferSource();s.buffer=noise;s.loop=true;const fl=ctx.createBiquadFilter();fl.type=type;fl.frequency.value=f;fl.Q.value=q;const g=ctx.createGain();g.gain.value=0;s.connect(fl).connect(g).connect(SFX);s.start();return[fl,g];}
function init(){if(ctx){ctx.state!=='running'&&ctx.resume();return;}
 const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;ctx=new AC({latencyHint:'interactive'});
 try{if(navigator.audioSession)navigator.audioSession.type='playback';}catch(e){}
 // iOS silent switch: a playing <audio> element moves the page to the "playback" session
 try{const a=new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAAAA');a.loop=true;a.setAttribute('playsinline','');a.play().catch(()=>{});}catch(e){}
 const comp=ctx.createDynamicsCompressor();comp.threshold.value=-14;comp.ratio.value=4;
 M=ctx.createGain();M.gain.value=muted?0:0.9;M.connect(comp).connect(ctx.destination);
 SFX=ctx.createGain();SFX.gain.value=0.8;SFX.connect(M);MUS=ctx.createGain();MUS.gain.value=0.32;MUS.connect(M);
 noise=mkNoise();[slideF,slideG]=loopNoise('bandpass',600,0.8);[windF,windG]=loopNoise('lowpass',300,0.5);[whF,whG]=loopNoise('bandpass',900,3);[grF,grG]=loopNoise('bandpass',3200,8);
 ctx.resume();nextT=ctx.currentTime+0.1;timer=setInterval(sched,25);}
function env(g,t,a,v,d){g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(v,t+a);g.gain.exponentialRampToValueAtTime(0.0001,t+a+d);}
function tone(f,f2,d,type='square',v=0.3,t=ctx.currentTime,bus=SFX){const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.setValueAtTime(f,t);if(f2)o.frequency.exponentialRampToValueAtTime(f2,t+d);env(g,t,0.005,v,d);o.connect(g).connect(bus);o.start(t);o.stop(t+d+0.05);}
function burst(f,d,v=0.4,type='lowpass',t=ctx.currentTime,bus=SFX,f2){const s=ctx.createBufferSource();s.buffer=noise;const fl=ctx.createBiquadFilter();fl.type=type;fl.frequency.setValueAtTime(f,t);if(f2)fl.frequency.exponentialRampToValueAtTime(f2,t+d);const g=ctx.createGain();env(g,t,0.004,v,d);s.connect(fl).connect(g).connect(bus);s.start(t,Math.random());s.stop(t+d+0.05);}
// music: 4-bar loop, Am-F-C-G, layers unlocked by intensity
const PROG=[[45,57,60,64],[41,53,57,60],[48,55,60,64],[43,55,59,62]],hz=n=>440*2**((n-69)/12);
function sched(){if(!ctx)return;while(nextT<ctx.currentTime+0.12){play16(step,nextT);nextT+=S16;step=(step+1)%64;}}
function play16(s,t){const ch=PROG[s>>4],b=s%16,lvl=I;
 if(b%4===0){tone(150,45,0.18,'sine',0.9,t,MUS);}
 if(b===4||b===12)burst(1800,0.12,lvl>0.2?0.35:0.2,'bandpass',t,MUS);
 if(b%2===0||lvl>0.5)burst(8000,0.03,b%4===2?0.18:0.08,'highpass',t,MUS);
 if(b%2===1||b%4===2){const o=ctx.createOscillator(),f=ctx.createBiquadFilter(),g=ctx.createGain();o.type='sawtooth';o.frequency.value=hz(ch[0]-12+(b%8===6?12:0));f.type='lowpass';f.frequency.value=300+lvl*1600;f.Q.value=6;env(g,t,0.005,0.35,S16*0.9);o.connect(f).connect(g).connect(MUS);o.start(t);o.stop(t+S16+0.05);}
 if(lvl>0.35&&b%2===0){const n=ch[1+((b>>1)%3)]+12;tone(hz(n),0,S16*1.6,'square',0.08+lvl*0.07,t,MUS);}
 if(lvl>0.75&&b%4===0)tone(hz(ch[1]+24),0,S16*3,'triangle',0.12,t,MUS);}
const A={init,
 get muted(){return muted},
 toggle(){muted=!muted;localStorage.setItem('pr_mute',muted?'1':'0');if(M)M.gain.setTargetAtTime(muted?0:0.9,ctx.currentTime,0.05);return muted;},
 update(s){if(!ctx)return;const t=ctx.currentTime,k=0.06,v=Math.min(1,s.v/38),play=s.play;
  slideG.gain.setTargetAtTime(play&&!s.air?0.04+v*0.18+Math.abs(s.steer)*0.25:0,t,k);
  slideF.frequency.setTargetAtTime(350+v*900+Math.abs(s.steer)*1400,t,k);slideF.Q.value=0.7+Math.abs(s.steer)*2;
  windG.gain.setTargetAtTime(play?v*v*0.22+(s.air?0.08:0):0,t,0.2);windF.frequency.setTargetAtTime(250+v*900,t,0.2);
  whG.gain.setTargetAtTime(play&&s.trick?0.28:0,t,0.03);whF.frequency.setTargetAtTime(600+Math.sin(t*25)*350+400,t,0.01);
  grG.gain.setTargetAtTime(play&&s.rail?0.35:0,t,0.03);grF.frequency.setTargetAtTime(2600+v*1500,t,0.05);I=play?Math.min(1,v*0.6+(s.combo-1)*0.15):0.1;},
 jump(){if(!ctx)return;burst(2500,0.18,0.35,'bandpass',undefined,SFX,600);tone(220,520,0.15,'triangle',0.15);},
 land(ok,pts){if(!ctx)return;burst(500,0.15,0.5);if(ok&&pts){const t=ctx.currentTime;[0,4,7,12].forEach((n,i)=>tone(hz(72+n),0,0.12,'square',0.12,t+0.05+i*0.06));}},
 combo(c){if(!ctx)return;const t=ctx.currentTime;tone(hz(76+c*2),hz(88+c*2),0.18,'sawtooth',0.1,t+0.3);},
 crash(tree){if(!ctx)return;burst(900,0.5,0.7,'lowpass',undefined,SFX,120);tone(160,40,0.4,'sawtooth',0.3);if(tree){burst(3000,0.25,0.3,'highpass');tone(90,50,0.25,'sine',0.6);}},
 start(){if(!ctx)return;const t=ctx.currentTime;[0,0.25,0.5].forEach(d=>tone(440,0,0.12,'square',0.15,t+d));tone(880,0,0.35,'square',0.2,t+0.75);},
 finish(){if(!ctx)return;const t=ctx.currentTime;[60,64,67,72,76,79,84].forEach((n,i)=>tone(hz(n),0,0.2,'square',0.13,t+i*0.08));},
 boost(){if(!ctx)return;burst(400,0.6,0.5,'bandpass',undefined,SFX,4000);tone(110,880,0.5,'sawtooth',0.15);},
 grind(on){if(!ctx)return;if(on){burst(5000,0.25,0.3,'highpass');tone(1800,1200,0.25,'sawtooth',0.05);}gr=on;},
 ui(){if(!ctx)return;tone(660,990,0.06,'square',0.1);},
 record(ms){return new Promise(r=>{const d=ctx.createMediaStreamDestination();M.connect(d);const mr=new MediaRecorder(d.stream),ch=[];mr.ondataavailable=e=>ch.push(e.data);mr.onstop=async()=>{const b=new Blob(ch);const fr=new FileReader();fr.onload=()=>r(fr.result);fr.readAsDataURL(b);};mr.start();setTimeout(()=>mr.stop(),ms);});}
};
window.AU=A;
['pointerdown','touchstart','keydown'].forEach(e=>addEventListener(e,init,{passive:true}));
})();
