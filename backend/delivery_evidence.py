"""Capture facts and transcript observations, never inferred speaking scores.

The pilot's transcription model provides no word timing or confidence. Sample
counts measure the submitted recording only; they cannot establish speech rate
or linguistic pauses. No raw audio is retained here.
"""
import re


def capture_evidence(samples, padding_samples, rate):
    return {'version':1, 'source':'server_pcm_samples',
            'capture_ms':(samples-padding_samples)*1000//rate,
            'recognition_confidence':'not_provided', 'configured_language':'en'}


def _examples(pattern, text):
    examples, seen = [], set()
    for match in re.finditer(pattern, text, re.IGNORECASE):
        value = match.group()
        if value.casefold() not in seen:
            examples.append(value)
            seen.add(value.casefold())
        if len(examples) == 3:break
    return examples


def describe_delivery(text, provenance):
    """Only accepted words and validated capture facts reach a coaching card."""
    if text is None:return None
    voice = isinstance(provenance, dict) and provenance.get('method') == 'voice'
    raw = provenance.get('delivery_evidence') if voice else None
    recording = None
    if (isinstance(raw, dict) and type(raw.get('version')) is int and raw['version'] == 1
            and raw.get('source') == 'server_pcm_samples'
            and type(raw.get('capture_ms')) is int and 0 < raw['capture_ms'] <= 125000
            and raw.get('recognition_confidence') == 'not_provided' and raw.get('configured_language') == 'en'):
        recording = {key:raw[key] for key in ('version','source','capture_ms','recognition_confidence','configured_language')}
    reason = ('typed_input' if not voice else 'capture_evidence_unavailable' if recording is None
              else 'recording_too_short' if recording['capture_ms'] < 3000
              else 'word_timing_and_confidence_unavailable')
    return {'input_method':'voice' if voice else 'typed', 'recording':recording,
            'observations':{'filler_examples':_examples(r'\b(?:u+h+m+|u+m+|u+h+)\b',text) if recording else [],
                            'repetition_examples':_examples(r'\b([\w\u2019\x27]+)\s+\1\b',text)},
            'speaking_rate':None, 'pauses':None, 'measurement_reason':reason}
