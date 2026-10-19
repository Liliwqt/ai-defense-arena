"""Temporary release scope during the two-checkpoint provider migration.

These are release gates, not environment toggles: old pilot configuration must
not revive a direct provider. Retained results and typed research remain usable.
"""

CODE_ONLY_AVAILABLE = False
VOICE_AVAILABLE = False
CODE_UNAVAILABLE = 'Code-only defense is temporarily unavailable. Choose Research paper or Research + code.'
