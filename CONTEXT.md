# AI Defense Arena

A team practices defending uploaded code or research with a panel of AI reviewers. Hosts organize defenses; teammates participate as defenders.

## Language

### Defense

**Room**:
A shared place where a host and up to three teammates prepare and participate in a defense. A room can contain successive defense runs.
_Avoid_: Run, session when referring to the shared room.

**Host account**:
The signed-in identity that owns a room and its host controls. A host's display name is separate from account identity.
_Avoid_: Defender name as account identity.

**Defender**:
A team member occupying one of the room's four defender seats; the host is also a defender. A teammate may participate without a host account.

**Defense run**:
One attempt at defending the uploaded material, with its own questions, answers and coaching. Restarting begins another run in the same room.
_Avoid_: Room, question when referring to a complete defense attempt.

**Defense turn**:
One grounded panelist question and its associated vote, possible clarifications and answer or unanswered outcome. An optional follow-up is a new turn.
_Avoid_: Clarification as an additional turn.

**Chosen defender**:
The online defender selected to answer the current question after the speaker vote. Selection may change after a disconnection.

**Clarification**:
An explanation, translation or example of the existing question that preserves its intent. It is neither the team's answer nor a follow-up question.

**Answer probe**:
A panelist's request for one important detail about an answer already given, with any defender reply remaining part of the same defense turn.
_Avoid_: Follow-up question (a new turn), clarification (the defender asks for an explanation).

**Grounded citation**:
An exact excerpt from accepted uploaded material with its validated location. It establishes the excerpt's origin, not the correctness of the panelist's interpretation.

**Research coverage**:
The discussion status of substantive topics identified in the research map. An addressed topic is sufficiently discussed, not proven correct.

### Sandbox access

**Top-up**:
An addition of credits to an account balance whose payment must be verified before credits are awarded. A browser return from checkout is not verification.
_Avoid_: Sandbox purchase, real-money purchase, deposit.

**Credit award**:
Test credits granted once for a verified sandbox purchase. A pending purchase has no credit award.

The authenticated, test-key-gated top-up simulation is an explicitly labeled
sandbox fixture exception. It uses the same once-only ledger but is not
evidence of provider payment; ordinary payment confirmation still requires
a verified webhook.

**Run reservation**:
Test credits held for a defense run before its first validated question appears. The reservation is charged on that question or released on opening failure.

**Run charge**:
The flat sandbox-credit cost finalized for a defense run when its first validated question appears. It is distinct from the purchase that originally awarded those credits.
_Avoid_: Purchase, per-question fee.

**Voucher access**:
An account grant allowing defense runs without spending credits. A changed or removed voucher revokes future access without undoing already authorized runs.

### Live tester access

**Tester**:
A signed-in host participating in the temporary live-payment release. A guest defender joining a room is a separate role.
_Avoid_: Guest defender, invited tester when no invitation is required.

**Live credit**:
A unit of defense access purchased through a verified real-money top-up. At the temporary tester rate, PHP 1 buys ten credits and a paid defense run costs ten; unused credits do not expire or change their count when future prices change.
_Avoid_: Peso balance, sandbox credit, demo credit.

**Top-up invitation**:
Permission for a signed-in host to purchase live credits during the temporary release. It is not required to redeem a voucher for free access.
_Avoid_: Room invitation, voucher, permission to join a defense.

**Credit return**:
Restoration of credits previously charged for a defense run, including a verified server interruption of an unfinished run. It does not refund the money paid for the original top-up.
_Avoid_: Payment refund, new top-up.

**Payment refund**:
Money returned for an earlier top-up payment. It is separate from restoring a defense run's credits.
_Avoid_: Credit return.

**Abandoned run**:
A defense run whose defenders have all remained disconnected for ten minutes while the service is operating. Abandonment does not qualify for the automatic credit return granted for a verified server interruption.
_Avoid_: Timed-out turn, server-interrupted run.

**Payment recovery**:
Confirmation of an already-paid top-up whose local receipt is still pending,
based on independently verified provider evidence. It neither creates a new
payment nor returns defense credits.
_Avoid_: Credit return, payment refund, payer-reported success.

**Unused top-up**:
A paid top-up whose awarded credits have not been spent. It is the ordinary
category eligible for an operator-reviewed money-refund request; eligibility
does not mean the refund has already reached the customer.
_Avoid_: Unpaid receipt, unused defense question.
