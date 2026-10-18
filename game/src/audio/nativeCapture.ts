import {useSyncExternalStore} from 'react';
import {isNativeShell} from '../lib/saveDefenseSummary';

let port:MessagePort|null=null;
let sequence=0;
let currentId:string|null=null;
let pending:{id:string;resolve:(release:()=>void)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}|null=null;
const changed=()=>window.dispatchEvent(new Event('defense-native-audio-ready'));
function post(value:object){try{port?.postMessage(JSON.stringify(value));}catch{/* Native document already left. */}}
function release(id:string){post({type:'cancel',id});if(currentId===id)currentId=null;}
function cancelPending(){
 if(currentId)release(currentId);
 if(pending){const old=pending;pending=null;clearTimeout(old.timer);old.reject(new Error('Microphone request cancelled. Start again or use typing.'));}
}
function nativeContainer(){
 const ua=navigator.userAgent;
 return isNativeShell() || /DefenseArenaAndroid\//.test(ua) || /Android.*;\s*wv\b/.test(ua)
   || /(?:iPhone|iPad).*AppleWebKit/.test(ua)&&!/Safari\//.test(ua);
}
export function voiceCaptureSupported(){
 return window===window.top && Boolean(typeof navigator.mediaDevices?.getUserMedia==='function' && typeof AudioContext!=='undefined'
  && typeof AudioWorkletNode!=='undefined' && (!nativeContainer()||port));
}
export function useVoiceCaptureSupported(){
 return useSyncExternalStore(callback=>{window.addEventListener('defense-native-audio-ready',callback);return()=>window.removeEventListener('defense-native-audio-ready',callback);},voiceCaptureSupported,()=>false);
}
window.addEventListener('message',(event:MessageEvent)=>{
 if(window!==window.top || event.data!=='defense-audio-port-v1' || event.ports.length!==1)return;
 if(event.source!==null && (event.source!==window||event.origin!==location.origin))return;
 cancelPending();port?.close();port=event.ports[0];
 port.onmessage=event=>{
  if(typeof event.data!=='string'||event.data.length>200)return;
  let body;try{body=JSON.parse(event.data);}catch{return;}
  if(!pending||body.id!==pending.id||!['prepared','denied'].includes(body.type))return;
  const request=pending;pending=null;clearTimeout(request.timer);
  if(body.type==='prepared')request.resolve(()=>release(request.id));
  else{release(request.id);request.reject(new Error('Microphone access was denied. Use typing or try again.'));}
 };
 port.start();changed();
});
window.addEventListener('defense-native-background',cancelPending);
window.addEventListener('pagehide',()=>{cancelPending();port?.close();port=null;changed();});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')cancelPending();});

/** Called only by explicit Start mic; no OS permission or media request on load. */
export async function prepareNativeCapture(current:()=>boolean):Promise<()=>void>{
 if(!nativeContainer())return()=>{};
 if(!port||window!==window.top)throw new Error('Voice requires an updated supported app. Use typing.');
 cancelPending();const id=`mic-${++sequence}`;currentId=id;
 const releaseIntent=await new Promise<()=>void>((resolve,reject)=>{
  const timer=setTimeout(()=>{if(pending?.id===id){pending=null;release(id);reject(new Error('Microphone permission timed out. Start again or type.'));}},30000);
  pending={id,resolve,reject,timer};post({type:'prepare',id});
 });
 if(!current()){releaseIntent();throw new Error('Voice capture was cancelled.');}
 return releaseIntent;
}
