import { useState } from 'react';
import type { AnswerCoachingCard, AnswerFeedback, Turn } from '../types';
import { ProbeExchange } from './ProbeExchange';

function Evidence({provenance}: {provenance?: Turn['input_provenance']}) {
  return <p className="coaching-evidence">{provenance?.method==='voice'
    ? 'Voice transcript · recognition may differ from speech. Audio measurements unavailable for pace or pauses.'
    : 'Typed answer · Audio measurements unavailable.'}</p>;
}
function Suggestions({feedback, title}: {feedback:AnswerFeedback;title:string}) {
  return <section aria-label={title} className="answer-suggestions">
    <h5>{title}</h5>
    {!!feedback.strengths.length && <><h6>What worked</h6><ul>{feedback.strengths.map((text,i)=><li key={i}>{text}</li>)}</ul></>}
    <h6>What to improve and why</h6><ul>{feedback.improvements.map((text,i)=><li key={i}>{text}</li>)}</ul>
    {feedback.stronger_answer && <><h6>{feedback.wording_basis==='conditional'?'Conditional scaffold · confirm missing facts':'Suggested wording'}</h6><p className="practice-wording">{feedback.stronger_answer}</p><p className="coaching-evidence">Practice suggestion; check the paper and your actual research decisions before using it.</p></>}
    {!!feedback.wording_examples.length && <p>Captured wording to practice: {feedback.wording_examples.map(word=>`“${word}”`).join(', ')}. These examples do not establish spoken filler totals.</p>}
    <h6>Practice task</h6><p>{feedback.practice_task}</p>
  </section>;
}
export function AnswerCoaching({cards}: {cards:AnswerCoachingCard[]}) {
  const [selected,setSelected]=useState(cards[0]?.turn ?? 0);
  const card=cards.find(card=>card.turn===selected) ?? cards[0];
  if(!card)return null;
  const index=cards.indexOf(card);
  return <section className="answer-coaching" aria-label="Detailed answer coaching">
    <h4>Practice each answer</h4><p>{cards.length} recorded question{cards.length===1?'':'s'} · complete coaching</p>
    <div className="coaching-selector"><label htmlFor="coaching-question">Review a question</label>
      <select id="coaching-question" value={card.turn} onChange={event=>setSelected(Number(event.target.value))}>
        {cards.map(item=><option key={item.turn} value={item.turn}>Question {item.turn+1} · {item.panelist}</option>)}
      </select>
      <div className="coaching-navigation"><button type="button" disabled={index===0} onClick={()=>setSelected(cards[index-1].turn)}>Previous question</button><button type="button" disabled={index===cards.length-1} onClick={()=>setSelected(cards[index+1].turn)}>Next question</button></div>
    </div>
    <section className="coaching-detail" aria-label="Question coaching" key={card.turn}>
      <h4 aria-live="polite">Question {card.turn+1} · {card.question}</h4>
      <details open><summary>Original answer and sources</summary>
        {card.original_answer!==null ? <><p><strong>{card.speaker_name ?? 'Defender'} · Original answer</strong></p><p className="original-answer">{card.original_answer}</p><Evidence provenance={card.input_provenance}/></> : <p>{card.timed_out?'Time expired without an answer.':'Ended before an answer was recorded.'}</p>}
        {card.citation && <blockquote><p>{card.citation.filename} · {card.citation.evidence_location || `Line ${card.citation.evidence_line}`}</p><p>{card.citation.evidence_text}</p></blockquote>}
        <ProbeExchange probe={card.probe} panelist={card.panelist}/>
        {card.probe?.reply!=null && <Evidence provenance={card.probe.input_provenance}/>}
      </details>
      <details open><summary>Improvements and practice</summary>
        <Suggestions feedback={card.feedback} title={card.original_answer===null?'Missed-answer practice':`${card.speaker_name ?? 'Defender'} · Answer coaching`}/>
        {card.probe_feedback && <Suggestions feedback={card.probe_feedback} title={`${card.probe?.speaker_name ?? 'Defender'} · Reply coaching`}/>}
      </details>
    </section>
  </section>;
}
