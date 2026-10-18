/* Raw mono PCM16, 100ms frames. No microphone playback or audio persistence. */
class PracticePCM extends AudioWorkletProcessor {
  constructor() {
    super(); this.buffer = new Int16Array(2400); this.length = 0; this.finished = false;
    this.port.onmessage = ({data}) => {
      if (data.type === 'flush') {
        if (this.length) this.port.postMessage(this.buffer.slice(0, this.length).buffer);
        this.length = 0; this.finished = true; this.port.postMessage({type:'flushed'});
      }
    };
  }
  process(inputs, outputs) {
    for (const output of outputs) for (const channel of output) channel.fill(0);
    if (!this.finished) for (const sample of inputs[0]?.[0] ?? []) {
      this.buffer[this.length++] = Math.round(Math.max(-1, Math.min(1, sample)) * (sample < 0 ? 32768 : 32767));
      if (this.length === this.buffer.length) { this.port.postMessage(this.buffer.buffer); this.buffer = new Int16Array(2400); this.length = 0; }
    }
    return !this.finished;
  }
}
registerProcessor('practice-pcm', PracticePCM);
