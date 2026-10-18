import { useState } from 'react';
import type { AnswerCoachingCard, AnswerFeedback, CoachingProgress, Turn } from '../types';
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
export function AnswerCoaching({cards,progress}: {cards:AnswerCoachingCard[];progress?:CoachingProgress|null}) {
  const turns=progress?Array.from({length:progress.cards_required},(_,i)=>i):cards.map(card=>card.turn);
  const [selected,setSelected]=useState(turns[0] ?? 0);
  const turn=turns.includes(selected)?selected:turns[0];
  if(turn===undefined)return null;
  const card=cards.find(card=>card.turn===turn);
  const index=turns.indexOf(turn);
  const pending=progress?.sections.find(section=>section.turns?.includes(turn));
  return <section className="answer-coaching" aria-label="Detailed answer coaching">
    <h4>Practice each answer</h4><p>{turns.length} recorded question{turns.length===1?'':'s'} · {progress?.completion_status && progress.completion_status!=='ready'?(['cancelled','returned','abandoned'].includes(progress.completion_status)?'incomplete coaching':'coaching in progress'):'complete coaching'}</p>
    <div className="coaching-selector"><label htmlFor="coaching-question">Review a question</label>
      <select id="coaching-question" value={turn} onChange={event=>setSelected(Number(event.target.value))}>
        {turns.map(i=><option key={i} value={i}>Question {i+1} · {cards.find(card=>card.turn===i)?.panelist ?? progress?.sections.find(section=>section.turns?.includes(i))?.status ?? 'pending'}</option>)}
      </select>
      <div className="coaching-navigation"><button type="button" disabled={index===0} onClick={()=>setSelected(turns[index-1])}>Previous question</button><button type="button" disabled={index===turns.length-1} onClick={()=>setSelected(turns[index+1])}>Next question</button></div>
    </div>
    <section className="coaching-detail" aria-label="Question coaching" key={turn}>
      <h4 aria-live="polite">Question {turn+1}{card?` · ${card.question}`:''}</h4>
      {!card ? <p role="status">{pending?.status==='failed'?'Coaching for this question failed. Ready sections are retained.':pending?.status==='cancelled'?'Coaching for this question ended before completion.':'Coaching for this question is still being prepared.'}</p> : <>
      <details open><summary>Original answer and sources</summary>
        {card.original_answer!==null ? <><p><strong>{card.speaker_name ?? 'Defender'} · Original answer</strong></p><p className="original-answer">{card.original_answer}</p><Evidence provenance={card.input_provenance}/></> : <p>{card.timed_out?'Time expired without an answer.':'Ended before an answer was recorded.'}</p>}
        {card.citation && <blockquote><p>{card.citation.filename} · {card.citation.evidence_location || `Line ${card.citation.evidence_line}`}</p><p>{card.citation.evidence_text}</p></blockquote>}
        <ProbeExchange probe={card.probe} panelist={card.panelist}/>
        {card.probe?.reply!=null && <Evidence provenance={card.probe.input_provenance}/>}
      </details>
      <details open><summary>Improvements and practice</summary>
        <Suggestions feedback={card.feedback} title={card.original_answer===null?'Missed-answer practice':`${card.speaker_name ?? 'Defender'} · Answer coaching`}/>
        {card.probe_feedback && <Suggestions feedback={card.probe_feedback} title={`${card.probe?.speaker_name ?? 'Defender'} · Reply coaching`}/>}
      </details></>}
    </section>
  </section>;
}
