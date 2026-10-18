import {prepareNativeCapture} from "./nativeCapture";
/** Browser media boundary. Speech drafts and audio never use browser storage. */
export async function startCapture(onFrame: (frame: ArrayBuffer) => void, onFailure: () => void, current: () => boolean) {
  if (!navigator.mediaDevices?.getUserMedia || typeof AudioContext === 'undefined' || typeof AudioWorkletNode === 'undefined') {
    throw new Error('Microphone capture is unavailable in this browser. Use typing.');
  }
  const releaseNative = await prepareNativeCapture(current);
  let stream:MediaStream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }, video: false }); }
  catch(error){releaseNative();throw error;}
  const stopTracks = () => {stream.getTracks().forEach(track => track.stop());releaseNative();};
  if (!current()) { stopTracks(); throw new Error('Voice capture was cancelled.'); }
  let context: AudioContext;
  try { context = new AudioContext({ sampleRate: 24000 }); }
  catch (error) { stopTracks(); throw error; }
  let node: AudioWorkletNode | null = null;
  let source: MediaStreamAudioSourceNode | null = null;
  let flushed: (() => void) | null = null;
  let stopped = false;
  function stop() {
    if (stopped) return;
    stopped = true; flushed?.(); flushed = null; stopTracks(); source?.disconnect(); node?.disconnect(); void context.close();
  }
  try {
    if (context.sampleRate !== 24000 || !context.audioWorklet) throw new Error('This browser cannot capture the required audio format. Use typing.');
    await context.audioWorklet.addModule(new URL('./pcm-worklet.js', import.meta.url).href);
    if (!current()) throw new Error('Voice capture was cancelled.');
    node = new AudioWorkletNode(context, 'practice-pcm');
    node.port.onmessage = event => {
      if (stopped) return;
      if (event.data instanceof ArrayBuffer) onFrame(event.data);
      else if (event.data?.type === 'flushed') flushed?.();
    };
    node.addEventListener('processorerror', onFailure);
    stream.getTracks().forEach(track => {track.addEventListener('ended', onFailure);track.addEventListener('mute', onFailure);});
    source = context.createMediaStreamSource(stream); source.connect(node); node.connect(context.destination);
    await context.resume();
    if (!current()) throw new Error('Voice capture was cancelled.');
    return { stop, async finish() {
      try {
        await new Promise<void>((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('Microphone finalization failed. Nothing was submitted; use typing.')), 1000);
          flushed = () => { clearTimeout(timer); resolve(); }; node!.port.postMessage({type:'flush'});
        });
      } finally { stop(); }
    }};
  } catch (error) { stop(); throw error; }
}
