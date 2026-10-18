import type {AnswerDelivery, CaptureEvidence, Turn} from '../types';

export function recordingLine(recording:CaptureEvidence):string {
 return `Measured recording: ${(recording.capture_ms/1000).toFixed(1)} seconds of submitted audio. This is recording duration, not speaking time.`;
}
export function deliveryLines(evidence:AnswerDelivery|undefined|null,provenance?:Turn['input_provenance']):string[]{
 if(!evidence)return [provenance?.method==='voice'?'Voice transcript · recognition may differ from speech. Audio measurements unavailable for pace or pauses.':'Typed answer · Audio measurements unavailable.'];
 const lines=[evidence.input_method==='voice'?'Voice transcript · recognition may differ from speech.':'Typed answer · Audio measurements unavailable.'];
 if(evidence.recording)lines.push(recordingLine(evidence.recording));
 if(evidence.input_method==='voice'){
  const reason=evidence.measurement_reason==='recording_too_short'?'the recording is too short, and this speech model provides no word timing or transcription confidence.':evidence.measurement_reason==='capture_evidence_unavailable'?'validated recording evidence is unavailable.':'the speech model supplies no word timing or transcription confidence.';
  lines.push(`Speaking rate and pauses unavailable: ${reason}`);
 }
 const observations=evidence.observations;
 if(observations.filler_examples.length)lines.push(`Transcript observation · possible hesitation wording: ${observations.filler_examples.map(word=>`“${word}”`).join(', ')}.`);
 if(observations.repetition_examples.length)lines.push(`Transcript observation · repeated wording: ${observations.repetition_examples.map(word=>`“${word}”`).join(', ')}.`);
 if(evidence.input_method==='voice')lines.push('Transcript examples may reflect recognition errors. They do not establish spoken filler totals; missing examples do not prove filler-free speech. Review meaning and language before changing wording.');
 return lines;
}
