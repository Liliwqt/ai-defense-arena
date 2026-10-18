import type { RoomState } from '../types';
export function coachedRoom(): RoomState {
  const first={turn:0,question:'Why this scope?',panelist:'Methodology Reviewer',original_answer:'Uhm, we will limit the claim.',speaker_name:'Alex',timed_out:false,ended_early:false,
    input_provenance:null,citation:{filename:'paper.md',evidence_line:1,evidence_text:'The proposal describes a campus pilot.'},
    probe:{id:'probe-one',request:'Which scope?',status:'answered' as const,references:[],reply:'The campus pilot.',speaker_name:'Sam',clarifications:[]},
    feedback:{strengths:['The claim has a stated boundary.'],improvements:['Lead with the boundary before explaining the reason.'],stronger_answer:'We will limit our claim to the campus pilot.',wording_basis:'supported' as const,practice_task:'Rehearse the claim, reason and source.',wording_examples:['Uhm']},
    probe_feedback:{strengths:['You identified the setting.'],improvements:['Link that setting to the planned evaluation.'],stronger_answer:'If supported, explain [why this setting fits the evaluation].',wording_basis:'conditional' as const,practice_task:'Explain the setting without adding unverified results.',wording_examples:[]}};
  const second={...first,turn:1,question:'How will consent work?',panelist:'Ethics Reviewer',original_answer:null,speaker_name:null,timed_out:true,probe:null,
    feedback:{strengths:[],improvements:['No answer was recorded.'],stronger_answer:null,wording_basis:'unanswered' as const,practice_task:'Locate the consent plan and practice explaining it.',wording_examples:[]},probe_feedback:null};
  return {room_code:'COACH1',defense_view_id:'run-coach',self_is_host:true,self_seat:0,selected_seat:null,
    players:[{seat:0,name:'Alex',is_host:true,online:true},{seat:1,name:'Sam',is_host:false,online:true}],
    phase:'complete',active_panelist:null,error:null,revision:1,files:['paper.md'],defense_type:'research',
    turns:[{panelist:first.panelist,question:first.question,answer:first.original_answer,answered_by:'Alex',filename:'paper.md',evidence_line:1,evidence_text:first.citation.evidence_text,probe:first.probe},
      {panelist:second.panelist,question:second.question,answer:null,answered_by:null,timed_out:true,filename:'paper.md',evidence_line:1,evidence_text:first.citation.evidence_text}],
    feedback_status:'ready',feedback:{summary:'The discussion established a limited scope; consent remains unanswered.',strengths:[],improvements:[],next_step:'Practice the unresolved explanation.',answer_cards:[first,second]}};
}
