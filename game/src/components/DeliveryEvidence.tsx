import type {AnswerDelivery, Turn} from '../types';
import {deliveryLines} from '../lib/deliveryEvidence';
export function DeliveryEvidence({evidence,provenance,speaker,reply=false}:{evidence?:AnswerDelivery|null;provenance?:Turn['input_provenance'];speaker:string;reply?:boolean}){
 return <section className="delivery-evidence" aria-label={`${speaker} · ${reply?'Reply':'Answer'} delivery evidence`}>
  <h5>Words and recording evidence</h5>
  {deliveryLines(evidence,provenance).map((line,i)=><p key={i} className="coaching-evidence">{line}</p>)}
 </section>;
}
