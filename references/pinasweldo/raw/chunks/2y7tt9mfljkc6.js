(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,41729,e=>{"use strict";var t=e.i(43476),r=e.i(71645),i=e.i(36884);let a=["#120f17","#2a0f0a","#9a3412","#f97316","#fed7aa"],n={linear:0,radial:1},o=`#version 300 es
out vec2 vUv;
void main() {
  vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
  vUv = p;
  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}`,l=`#version 300 es
precision highp float;
precision highp int;
uniform float uAspect;
uniform float uTime;
uniform vec3 uRamp[8];
uniform int uCount;
uniform int uType;
uniform vec2 uDir;
uniform float uExtent;
uniform float uBands;
uniform float uSoftness;
uniform float uFlow;
uniform float uScale;
uniform float uSilk;
uniform vec4 uStir[24];
uniform float uStirWeight[24];
uniform vec4 uTwirl[4];
uniform vec2 uSeed;
uniform float uContrast;
uniform float uSaturation;
uniform float uSettle;
uniform float uReveal;
in vec2 vUv;
out vec4 outColor;

vec2 hash2(vec2 p) {
  vec3 q = fract(vec3(p.xyx) * vec3(0.1031, 0.103, 0.0973));
  q += dot(q, q.yzx + 33.33);
  return fract((q.xx + q.yz) * q.zy) * 2.0 - 1.0;
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
  float a = dot(hash2(i), f);
  float b = dot(hash2(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0));
  float c = dot(hash2(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0));
  float d = dot(hash2(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0));
  return 0.5 + 0.5 * mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

vec2 drift(vec2 p, float t) {
  vec2 w1 = vec2(
    noise(p * 0.85 + vec2(t * 0.11, t * 0.07)),
    noise(p * 0.85 + vec2(4.1, 1.7) - vec2(t * 0.08, t * 0.12))
  );
  vec2 w2 = vec2(
    noise(p * 1.55 + w1 * 1.8 + vec2(1.3, 7.1) + t * 0.05),
    noise(p * 1.55 + w1 * 1.8 + vec2(6.4, 2.2) - t * 0.06)
  );
  return (w1 - 0.5) * 1.1 + (w2 - 0.5) * 0.55;
}

vec2 warp(vec2 p) {
  vec2 q = p / uScale;
  if (uType == 1) {
    float turn = uTime * 0.35;
    q = mat2(cos(turn), sin(turn), -sin(turn), cos(turn)) * q;
  } else {
    q += vec2(-uDir.y, uDir.x) * uTime * 0.45;
  }
  return p + drift(q + uSeed, uTime) * uFlow * uScale * uSettle;
}

float coord(vec2 p) {
  vec2 w = warp(p);
  return uType == 1 ? 1.0 - length(w) * 1.1 : dot(w, uDir) / uExtent + 0.5;
}

vec3 labToRgb(vec3 lab) {
  float l = lab.x + 0.3963377774 * lab.y + 0.2158037573 * lab.z;
  float m = lab.x - 0.1055613458 * lab.y - 0.0638541728 * lab.z;
  float s = lab.x - 0.0894841775 * lab.y - 1.2914855480 * lab.z;
  l = l * l * l;
  m = m * m * m;
  s = s * s * s;
  return vec3(
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
  );
}

vec3 encode(vec3 c) {
  c = clamp(c, 0.0, 1.0);
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}

void main() {
  vec2 p = (vUv - 0.5) * vec2(uAspect, 1.0);
  for (int i = 0; i < 24; i++) {
    float w = uStirWeight[i];
    if (w <= 0.0) continue;
    vec2 d = p - uStir[i].xy;
    p -= uStir[i].zw * w * exp(-dot(d, d) / 0.045);
  }
  for (int i = 0; i < 4; i++) {
    float angle = uTwirl[i].z;
    if (angle == 0.0) continue;
    vec2 d = p - uTwirl[i].xy;
    float a = angle * exp(-dot(d, d) / (uTwirl[i].w * uTwirl[i].w));
    float c = cos(a);
    float s = sin(a);
    p = uTwirl[i].xy + mat2(c, -s, s, c) * d;
  }
  float raw = coord(p);
  float s = raw;
  if (uBands > 1.0) {
    s *= uBands;
    float cycle = floor(s);
    s = fract(s);
    if (mod(cycle, 2.0) > 0.5) s = 1.0 - s;
  }
  s = clamp(s, 0.0, 1.0);
  float scaled = s * float(uCount - 1);
  int index = int(min(floor(scaled), float(uCount - 2)));
  float f = scaled - float(index);
  float edge = max(uSoftness * 0.5, fwidth(scaled) * 0.75);
  float shaped = smoothstep(0.5 - edge, 0.5 + edge, f);
  vec3 from = uRamp[0];
  vec3 to = uRamp[1];
  for (int i = 0; i < 7; i++) {
    if (i == index) {
      from = uRamp[i];
      to = uRamp[i + 1];
    }
  }
  vec3 lab = mix(from, to, shaped);
  if (uSilk > 0.0) {
    vec2 grad = vec2(coord(p + vec2(0.004, 0.0)) - raw, coord(p + vec2(0.0, 0.004)) - raw) / 0.004;
    vec2 slope = grad * sin(3.14159265 * clamp(raw, 0.0, 1.0) * uBands) * uSilk * 4.0;
    vec3 normal = normalize(vec3(-slope, 1.0));
    vec3 light = normalize(vec3(-uDir.y, uDir.x, 1.2));
    float diffuse = dot(normal, light) - light.z;
    lab = uRamp[0] + (lab - uRamp[0]) * (1.0 + (diffuse * 0.35 + max(diffuse, 0.0) * diffuse * 0.6) * uSilk);
  }
  lab = mix(uRamp[0], lab, smoothstep(0.0, 1.0, uReveal * 1.5 - length(vUv - 0.5) * 0.6));
  lab.x = (lab.x - 0.55) * uContrast + 0.55;
  lab.yz *= uSaturation;
  outColor = vec4(encode(labToRgb(lab)), 1.0);
}`,u=`#version 300 es
precision highp float;
uniform sampler2D uField;
uniform float uGrain;
uniform float uGrainSize;
uniform float uFrame;
in vec2 vUv;
out vec4 outColor;

float hash(vec2 p) {
  vec3 q = fract(vec3(p.xyx) * 0.1031);
  q += dot(q, q.yzx + 33.33);
  return fract((q.x + q.y) * q.z);
}

float clump(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void main() {
  vec3 color = texture(uField, vUv).rgb;
  vec2 pixel = gl_FragCoord.xy + uFrame * vec2(17.0, 59.0);
  float fine = hash(pixel) + hash(pixel + 7.13) - 1.0;
  float coarse = (clump(pixel / max(uGrainSize, 1.0)) - 0.5) * 2.0;
  float grain = mix(fine, coarse, clamp(uGrainSize - 1.0, 0.0, 1.0) * 0.8);
  float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
  color += grain * uGrain * (0.45 + 2.2 * luma * (1.0 - luma));
  outColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}`,c=(e,t,r)=>Math.min(r,Math.max(t,e)),f=e=>e<=.04045?e/12.92:((e+.055)/1.055)**2.4,s=(e,t,r)=>{let i=e.createShader(t);return i?(e.shaderSource(i,r),e.compileShader(i),e.getShaderParameter(i,e.COMPILE_STATUS))?i:(e.deleteShader(i),null):null},m=(e,t)=>{let r=s(e,e.VERTEX_SHADER,o),i=s(e,e.FRAGMENT_SHADER,t),a=e.createProgram();if(!r||!i||!a)return null;if(e.attachShader(a,r),e.attachShader(a,i),e.linkProgram(a),e.deleteShader(r),e.deleteShader(i),!e.getProgramParameter(a,e.LINK_STATUS))return e.deleteProgram(a),null;let n={},l=e.getProgramParameter(a,e.ACTIVE_UNIFORMS);for(let t=0;t<l;t++){let r=e.getActiveUniform(a,t);if(!r)continue;let i=r.name.replace(/\[0\]$/,"");n[i]=e.getUniformLocation(a,i)}return{program:a,uniforms:n}},d=({colors:e=a,type:i="linear",angle:o=55,bands:s=1,speed:d=1,flow:h=.8,scale:v=1,softness:p=1,silk:g=.35,grainAmount:x=.08,grainSize:w=1.2,grainAnimated:E=!0,contrast:T=1,saturation:y=1,variation:b=0,interactive:R=!0,stir:S=1,clickSwirl:M=!0,intro:A=!0,lightMode:F=!1,dpr:U,className:_="",style:D,...P})=>{let C=(0,r.useRef)(null),q=(0,r.useRef)(null),z=(0,r.useRef)(null),L=(Array.isArray(e)&&e.length?e:a).slice(0,8),I={colors:L.length>1?L:[L[0],L[0]],type:n[i]??0,angle:o,bands:c(s,1,8),speed:Math.max(0,d),flow:c(h,0,3),scale:c(v,.25,3),softness:c(p,0,1),silk:c(g,0,1),grainAmount:c(x,0,.5),grainSize:c(w,.5,4),grainAnimated:E,contrast:c(T,.2,2),saturation:c(y,0,2),variation:Math.max(0,b),interactive:R,stir:c(S,0,2),clickSwirl:M,intro:A,lightMode:F,dpr:U},B=(0,r.useRef)(I);return B.current=I,(0,r.useEffect)(()=>{let e=C.current,t=q.current,r=t?.getContext("webgl2",{alpha:!1,antialias:!1,depth:!1,stencil:!1});if(!e||!t||!r)return;let i=m(r,l),a=m(r,u);if(!i||!a)return;let n=i.uniforms,o=a.uniforms,s=r.createVertexArray(),d=r.createTexture();r.bindTexture(r.TEXTURE_2D,d),r.texParameteri(r.TEXTURE_2D,r.TEXTURE_MIN_FILTER,r.LINEAR),r.texParameteri(r.TEXTURE_2D,r.TEXTURE_MAG_FILTER,r.LINEAR),r.texParameteri(r.TEXTURE_2D,r.TEXTURE_WRAP_S,r.CLAMP_TO_EDGE),r.texParameteri(r.TEXTURE_2D,r.TEXTURE_WRAP_T,r.CLAMP_TO_EDGE);let h=r.createFramebuffer(),v={width:0,height:0},p=document.createElement("canvas").getContext("2d",{willReadFrequently:!0}),g=new Map,x=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches??!1,w={width:1,height:1,ratio:1},E=new Float32Array(24),T=new Float32Array(96),y=new Float32Array(24),b=new Float32Array(16),R=[],S=[],M={x:.5,y:.5,sx:.5,sy:.5,vx:0,inside:!1,fresh:!0},A="",F=0,U=B.current.intro&&!x?0:1,_=0,D=0,P=0,L=0,I=!0,G=()=>{let e=B.current,l=w.width/w.height;(()=>{let e=B.current,t=`${e.colors.join(",")}|${e.lightMode}`;if(t===A)return;A=t;let r=e.colors.map(e=>(([e,t,r])=>{let i=f(e),a=f(t),n=f(r),o=Math.cbrt(.4122214708*i+.5363325363*a+.0514459929*n),l=Math.cbrt(.2119034982*i+.6806995451*a+.1073969566*n),u=Math.cbrt(.0883024619*i+.2817188376*a+.6299787005*n);return[.2104542553*o+.793617785*l-.0040720468*u,1.9779984951*o-2.428592205*l+.4505937099*u,.0259040371*o+.7827717662*l-.808675766*u]})((e=>{let t=String(e),r=g.get(t);if(r)return r;let i=[0,0,0],a=/^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(t.trim());if(a){let e=3===a[1].length?a[1].replace(/./g,e=>e+e):a[1];return i=[0,2,4].map(t=>parseInt(e.slice(t,t+2),16)/255),g.set(t,i),i}if(p){p.clearRect(0,0,1,1),p.fillStyle="#000000",p.fillStyle=t,p.fillRect(0,0,1,1);let[e,r,a]=p.getImageData(0,0,1,1).data;i=[e/255,r/255,a/255]}return g.set(t,i),i})(e)));if(e.lightMode){let e=r.map(([e])=>.1>Math.abs(e-r[0][0])),t=r.filter((t,r)=>!e[r]).reverse();r.forEach((r,i)=>{let[a,n,o]=e[i]?[1,0,0]:t.shift();E.set([a+(1-a)*.2,.8*n,.8*o],3*i)})}else r.forEach((e,t)=>E.set(e,3*t))})(),r.bindVertexArray(s),r.disable(r.BLEND),r.bindFramebuffer(r.FRAMEBUFFER,h),r.viewport(0,0,v.width,v.height),r.useProgram(i.program),r.uniform1f(n.uAspect,l),r.uniform1f(n.uTime,F),r.uniform3fv(n.uRamp,E),r.uniform1i(n.uCount,e.colors.length);let u=e.angle*Math.PI/180;r.uniform1i(n.uType,e.type),r.uniform2f(n.uDir,Math.sin(u),Math.cos(u)),r.uniform1f(n.uExtent,l*Math.abs(Math.sin(u))+Math.abs(Math.cos(u))),r.uniform1f(n.uBands,e.bands),r.uniform1f(n.uSoftness,e.softness),r.uniform1f(n.uFlow,e.flow),r.uniform1f(n.uScale,e.scale),r.uniform1f(n.uSilk,e.silk),r.uniform4fv(n.uStir,T),r.uniform1fv(n.uStirWeight,y),r.uniform4fv(n.uTwirl,b),r.uniform2f(n.uSeed,3.17*e.variation,1.91*e.variation),r.uniform1f(n.uContrast,e.contrast),r.uniform1f(n.uSaturation,e.saturation),r.uniform1f(n.uSettle,U*U*(3-2*U)),r.uniform1f(n.uReveal,U),r.drawArrays(r.TRIANGLES,0,3),r.bindFramebuffer(r.FRAMEBUFFER,null),r.viewport(0,0,t.width,t.height),r.useProgram(a.program),r.activeTexture(r.TEXTURE0),r.bindTexture(r.TEXTURE_2D,d),r.uniform1i(o.uField,0),r.uniform1f(o.uGrain,e.grainAmount),r.uniform1f(o.uGrainSize,e.grainSize*w.ratio),r.uniform1f(o.uFrame,_),r.drawArrays(r.TRIANGLES,0,3)},X=()=>{let i=B.current;w.width=Math.max(1,e.clientWidth),w.height=Math.max(1,e.clientHeight),w.ratio=Math.min(i.dpr||window.devicePixelRatio||1,2),t.width=Math.max(1,Math.round(w.width*w.ratio)),t.height=Math.max(1,Math.round(w.height*w.ratio));let a=Math.max(1,Math.round(t.width/2)),n=Math.max(1,Math.round(t.height/2));(a!==v.width||n!==v.height)&&(v.width=a,v.height=n,r.bindTexture(r.TEXTURE_2D,d),r.texImage2D(r.TEXTURE_2D,0,r.RGBA8,a,n,0,r.RGBA,r.UNSIGNED_BYTE,null),r.bindFramebuffer(r.FRAMEBUFFER,h),r.framebufferTexture2D(r.FRAMEBUFFER,r.COLOR_ATTACHMENT0,r.TEXTURE_2D,d,0),r.bindFramebuffer(r.FRAMEBUFFER,null)),G(),N()},k=e=>{if(P=0,!I||document.hidden)return;let t=B.current,r=L?c((e-L)/1e3,.001,.05):1/60;L=e,x||(F+=r*t.speed*.16),U<1&&(U=Math.min(1,U+r/1.6)),D+=r,t.grainAnimated&&!x&&D>1/24&&(D=0,_=(_+1)%97),((e,t)=>{let r=B.current,i=1-Math.exp(-e/.06),a=M.sx,n=M.sy;M.sx+=(M.x-M.sx)*i,M.sy+=(M.y-M.sy)*i;let o=(M.sx-a)/e*t,l=(M.sy-n)/e;M.vx=o;let u=R[0];if(R.forEach(t=>{t.done&&(t.age+=e)}),r.interactive&&M.inside&&Math.hypot(o,l)>.02&&!x){(!u||u.done)&&(R.unshift({x:0,y:0,vx:0,vy:0,age:0,grow:0,done:!1}),R.length>24&&R.pop());let r=R[0];r.x=(M.sx-.5)*t,r.y=M.sy-.5,r.vx=o,r.vy=l,r.grow=Math.min(1,r.grow+e/.06),r.done=r.grow>=1}else u&&(u.done=!0);for(;R.length&&R[R.length-1].age>1.3;)R.pop();for(let e=0;e<24;e++){let t=R[e];if(!t){y[e]=0;continue}let i=1-t.age/1.3,a=Math.min(1,2.2/Math.max(Math.hypot(t.vx,t.vy),.001));T.set([t.x,t.y,t.vx*a,t.vy*a],4*e),y[e]=i*i*t.grow*r.stir*.05}for(S.forEach(t=>{t.age+=e});S.length&&S[S.length-1].age>2.6;)S.pop();for(let e=0;e<4;e++){let t=S[e];if(!t){b[4*e+2]=0;continue}let r=t.age/2.6,i=Math.min(1,t.age/.18)*(1-r)*(1-r);b.set([t.x,t.y,2.4*t.direction*i,.16+.1*Math.min(1,t.age/.5)],4*e)}})(r,w.width/w.height),G(),!x&&(t.speed>0||t.grainAnimated)||U<1||R.length>0||S.length>0?P=requestAnimationFrame(k):L=0};function N(){P||!I||document.hidden||(P=requestAnimationFrame(k))}let O=t=>{let r=e.getBoundingClientRect(),i=(t.clientX-r.left)/Math.max(1,r.width),a=1-(t.clientY-r.top)/Math.max(1,r.height);M.inside=i>=0&&i<=1&&a>=0&&a<=1,M.x=i,M.y=a,(M.fresh||!M.inside)&&(M.sx=i,M.sy=a,M.fresh=!1)},$=e=>{O(e),(M.inside||R.length)&&N()},j=e=>{O(e);let t=B.current;M.inside&&t.clickSwirl&&!x&&(S.unshift({x:(M.x-.5)*(w.width/w.height),y:M.y-.5,age:0,direction:M.vx<0?1:-1}),S.length>4&&S.pop(),N())},V=()=>{M.inside=!1},W=()=>{L=0,N()},H=new ResizeObserver(X);H.observe(e);let K=new IntersectionObserver(e=>{(I=e.some(e=>e.isIntersecting))&&(L=0,N())});return K.observe(e),window.addEventListener("pointermove",$,{passive:!0}),window.addEventListener("pointerdown",j,{passive:!0}),document.documentElement.addEventListener("pointerleave",V),document.addEventListener("visibilitychange",W),X(),z.current=N,()=>{cancelAnimationFrame(P),z.current=null,H.disconnect(),K.disconnect(),window.removeEventListener("pointermove",$),window.removeEventListener("pointerdown",j),document.documentElement.removeEventListener("pointerleave",V),document.removeEventListener("visibilitychange",W),r.deleteTexture(d),r.deleteFramebuffer(h),r.deleteVertexArray(s),r.deleteProgram(i.program),r.deleteProgram(a.program)}},[]),(0,r.useEffect)(()=>{z.current?.()}),(0,t.jsx)("div",{ref:C,className:`grainient-container${_?` ${_}`:""}`,style:D,...P,children:(0,t.jsx)("canvas",{ref:q,className:"grainient-canvas","aria-hidden":"true"})})},h=i.Y;e.s(["default",0,function({tone:e}){let i=function(){let[e,t]=(0,r.useState)(!1);return(0,r.useEffect)(()=>{let e=()=>t("dark"===document.documentElement.dataset.theme);e();let r=new MutationObserver(e);return r.observe(document.documentElement,{attributes:!0,attributeFilter:["data-theme"]}),()=>r.disconnect()},[]),e}();return(0,t.jsx)("div",{"aria-hidden":"true",className:"estimate-backdrop pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]",style:{background:`linear-gradient(145deg, ${h[i?"dark":"light"][e].join(", ")})`},children:(0,t.jsx)(d,{colors:[...h[i?"dark":"light"][e]],angle:55,speed:.35,flow:.35,silk:.2,grainAmount:.05},`${e}-${i}`)})}],41729)},25939,function(e){e.n(e.i(41729))}]);