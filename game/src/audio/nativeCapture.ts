import {useSyncExternalStore} from 'react';
import {isNativeShell} from '../lib/saveDefenseSummary';

type IosAudioHandler = {postMessage: (value: {type:string;id:string}) => unknown};
type NativeReply = {type?:string;id?:string};

let port:MessagePort|null=null;
let sequence=0;
let currentId:string|null=null;
let pending:{id:string;resolve:(release:()=>void)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}|null=null;
let iosPending:{id:string;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}|null=null;
const changed=()=>window.dispatchEvent(new Event('defense-native-audio-ready'));
function post(value:object){try{port?.postMessage(JSON.stringify(value));}catch{/* Native document already left. */}}
function release(id:string){post({type:'cancel',id});if(currentId===id)currentId=null;}
function iosAudioHandler():IosAudioHandler|null{
 const handlers=(window as unknown as {webkit?:{messageHandlers?:{defenseAudio?:IosAudioHandler}}}).webkit?.messageHandlers;
 const handler=handlers?.defenseAudio;
 return handler&&typeof handler.postMessage==='function'?handler:null;
}
function iosCancel(id:string){
 try{Promise.resolve(iosAudioHandler()?.postMessage({type:'cancel',id})).catch(()=>{/* Native document already left. */});}
 catch{/* Native document already left. */}
}
function cancelPending(){
 if(currentId)release(currentId);
 if(pending){const old=pending;pending=null;clearTimeout(old.timer);old.reject(new Error('Microphone request cancelled. Start again or use typing.'));}
 if(iosPending){const old=iosPending;iosPending=null;clearTimeout(old.timer);iosCancel(old.id);old.reject(new Error('Microphone request cancelled. Start again or use typing.'));}
}
function nativeContainer(){
 const ua=navigator.userAgent;
 return isNativeShell() || /DefenseArenaAndroid\//.test(ua) || /Android.*;\s*wv\b/.test(ua)
   || /(?:iPhone|iPad).*AppleWebKit/.test(ua)&&!/Safari\//.test(ua);
}
export function voiceCaptureSupported(){
 return window===window.top && Boolean(typeof navigator.mediaDevices?.getUserMedia==='function' && typeof AudioContext!=='undefined'
  && typeof AudioWorkletNode!=='undefined' && (!nativeContainer()||port||iosAudioHandler()));
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

// iOS WKWebView has no MessagePort. The native reply bridge resolves only after
// the explicit Start-mic action has passed native permission and lifecycle checks.
async function prepareIosCapture(handler:IosAudioHandler,current:()=>boolean):Promise<()=>void>{
 cancelPending();const id=`mic-${++sequence}`;
 const reply=await new Promise<NativeReply>((resolve,reject)=>{
  const timer=setTimeout(()=>{
   if(iosPending?.id===id){iosPending=null;iosCancel(id);reject(new Error('Microphone permission timed out. Start again or type.'));}
  },30000);
  iosPending={id,reject,timer};
  try{
   Promise.resolve(handler.postMessage({type:'prepare',id})).then(value=>resolve(value as NativeReply),reject).finally(()=>{
    if(iosPending?.id===id){clearTimeout(timer);iosPending=null;}
   });
  }catch(error){
   clearTimeout(timer);iosPending=null;
   reject(error instanceof Error?error:new Error('Microphone request failed. Start again or use typing.'));
  }
 });
 if(!reply||reply.id!==id||(reply.type!=='prepared'&&reply.type!=='denied'))throw new Error('Voice requires an updated supported app. Use typing.');
 if(reply.type!=='prepared')throw new Error('Microphone access was denied. Use typing or try again.');
 if(!current()){iosCancel(id);throw new Error('Voice capture was cancelled.');}
 return()=>iosCancel(id);
}

/** Called only by explicit Start mic; no OS permission or media request on load. */
export async function prepareNativeCapture(current:()=>boolean):Promise<()=>void>{
 if(!nativeContainer())return()=>{};
 if(window!==window.top)throw new Error('Voice requires an updated supported app. Use typing.');
 const ios=iosAudioHandler();
 if(ios)return prepareIosCapture(ios,current);
 if(!port)throw new Error('Voice requires an updated supported app. Use typing.');
 cancelPending();const id=`mic-${++sequence}`;currentId=id;
 const releaseIntent=await new Promise<()=>void>((resolve,reject)=>{
  const timer=setTimeout(()=>{if(pending?.id===id){pending=null;release(id);reject(new Error('Microphone permission timed out. Start again or type.'));}},30000);
  pending={id,resolve,reject,timer};post({type:'prepare',id});
 });
 if(!current()){releaseIntent();throw new Error('Voice capture was cancelled.');}
 return releaseIntent;
}
