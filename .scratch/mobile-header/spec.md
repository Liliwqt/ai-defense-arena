# Compact mobile defense-room header

Status: ready-for-human
Date: 2026-10-06
Working branch: feature/question-first-room

## Problem Statement

On a phone, the defense-room header contains a title, room-code box, progress
box, research-coverage box and several text buttons. These wrap into multiple
rows and use space that defenders need for panelist questions, grounded citations
and typing. The vote or answer timer is mixed among those controls rather than
consistently centered. Hosts and defenders need a compact header whose essential
controls are recognizable, reachable and stable throughout a defense run.

Portrait support is already implemented in the shared website. This checkpoint
refines that existing mobile layout, including its landscape and keyboard-sized
states, rather than creating another interface or native screen.

## Solution

Use one compact mobile header row: a Settings icon on the left, a centered
phase/countdown or factual status in the middle, and an Account icon on the right.
Settings opens the existing Controls drawer; Account opens the existing Account
area. Move room information and Transcript access into Controls. Remove the
mobile title and redundant header progress/coverage boxes, keeping the question
number on the question card and research coverage accessible in Controls.

During voting and answering, show VOTE or ANSWER with the remaining time. During
submission interpretation preserve the actual paused-time indication. Between
questions, show a short status derived from the room's real phase, such as
Preparing question…, Reviewing answer… or Complete. Use the recovered space for
the existing question/citation reading area, while keeping the seat strips and
bottom Vote/Answer and Team Chat dock.

## User Stories

1. As a mobile defender, I want a single compact header row, so that more of the panelist question and grounded citation fits on my screen.
2. As a mobile defender, I want the countdown centered between two controls, so that I can locate the time remaining immediately.
3. As a mobile defender, I want VOTE beside the voting countdown, so that I understand I am choosing a speaker.
4. As the chosen defender, I want ANSWER beside the answer countdown, so that I understand the time available for my response.
5. As a defender who submitted text for interpretation, I want the retained paused answer time labeled PAUSED, so that I do not mistake interpretation for a running answer clock.
6. As a defender near a deadline, I want the existing urgent indication and written phase label, so that urgency remains understandable without relying on color.
7. As a mobile host, I want a recognizable Settings icon to open Controls, so that I can manage the room without a long header button.
8. As a mobile participant, I want a recognizable Account icon to open Account, so that I can reach sign-in and private account information.
9. As a guest defender, I want Controls and Account navigation to remain available without implying I have host permissions, so that navigation does not change authorization.
10. As a host or defender, I want the room code available in Controls, so that I can find and share it after its header box is removed.
11. As a research participant, I want the addressed-topic count and coverage map in Controls, so that research progress remains inspectable without crowding the header.
12. As a defender, I want the current question number on the question card, so that I know my place without a duplicate progress box.
13. As a research participant, I want the approved maximum shown with the current question number, so that longer defenses retain their existing progress meaning.
14. As a code-project participant, I want question progress to retain its variable-length meaning, so that the layout does not imply a fixed total.
15. As a mobile participant, I want a clearly labeled Transcript action inside Controls, so that I can review dialogue and coaching without another header icon.
16. As a participant changing drawer sections, I want keyboard focus to stay inside the open dialog and return appropriately when dismissed, so that navigation remains predictable.
17. As a first-time host or teammate, I want create/join setup to open as it currently does, so that the simplified header does not conceal how to begin.
18. As a participant awaiting the opening question, I want Preparing question… in the center, so that I know the panel has not published a question yet.
19. As a defender who answered, I want Reviewing answer… while the next question is generated, so that the status reflects the accepted response.
20. As a defender whose turn expired, I want a neutral missed-turn review status, so that the interface does not claim an answer was given.
21. As a research host preparing a coverage plan, I want a mapping status rather than a question-generation claim, so that planning and starting remain distinct.
22. As a participant encountering an AI error, I want a retry-needed or paused status with existing recovery controls, so that a failure is not presented as ongoing work.
23. As a participant after the defense ends, I want Complete in the center and the existing coaching state visible in its usual place, so that completion does not imply coaching has already finished.
24. As a phone user rotating the screen, I want the same compact navigation and centered timer in portrait and landscape, so that controls remain familiar.
25. As a defender opening the keyboard, I want the header, question reading area and bottom composer to remain reachable, so that typing does not hide essential controls.
26. As a defender switching between drawers, rotation and keyboard states, I want my same-turn answer draft preserved, so that a layout change cannot discard my work.
27. As a screen-reader user, I want meaningful accessible names for icon buttons and timer/status text, so that icons do not become unexplained controls.
28. As a touch or keyboard user, I want comfortable icon targets and visible focus, so that compact presentation does not make actions difficult to use.
29. As a user with enlarged text, I want statuses and question content reachable without page-level horizontal overflow, so that readability does not require reducing my text size.
30. As a browser or WebView participant, I want the same shared website layout, so that phone browsers and installed apps do not diverge.
31. As a desktop participant, I want my existing header controls and information retained, so that the mobile refinement does not remove useful desktop navigation.
32. As a project owner, I want a local preview and honest verification evidence before publication, so that I can review the change without an unexpected deployment.

## Implementation Decisions

- Extend the existing shared room header and mobile-responsive styles. Apply the
  compact arrangement within the existing mobile breakpoint, at widths up to
  900 CSS pixels, for portrait, landscape and reduced visible-viewport height.
  Keep the larger desktop header's current content and navigation.
- Use a three-part layout with equal-width icon-control areas on each side.
  Center the timer/status within the available viewport, independent of label
  lengths. The header does not grow additional rows of pills; a longer center
  status may wrap within its own bounded cell without clipping or overlaying
  the controls.
- Settings is a navigation shortcut to the existing Controls dialog, not a new
  settings product. Account opens the existing Account dialog. Both remain
  reachable before joining and during a defense. Keep visible mobile labels
  icon-only, with stable accessible names identifying Settings/room controls
  and Account. Use a recognizable gear and person icon without a new dependency.
- Give both header controls touch areas of at least 44 by 44 CSS pixels and
  visible focus. Do not shrink those targets when the keyboard opens. Retain
  the existing theme, surfaces and focus/status colors.
- Hide the mobile brand/title, room-code pill, resolved/question-progress pill,
  research-coverage pill and direct Transcript header button. Hidden desktop
  controls must not remain in the mobile keyboard focus order or accessible
  navigation as duplicate actions.
- Retain the room-code display already available in Controls. Make the addressed
  topic count inspectable alongside the existing coverage map there, preserving
  its meaning: addressed describes discussion coverage, not research correctness.
  Code-only rooms do not acquire research coverage or a fixed question total.
- Keep current question numbering on the question card, including the approved
  research budget when present. Do not duplicate the progress pill in the mobile
  header or change defense-turn accounting and question budgets.
- Add a clearly labeled Transcript action to Controls that switches the existing
  dialog to its Transcript content. Keep Transcript readable by hosts and guests
  and preserve its existing empty/partial/completed states, export and coaching.
  This is navigation only; do not introduce another panel, route or export format.
- Preserve dialog focus trapping, Escape dismissal and scrim behavior. Switching
  Controls to Transcript moves focus into the destination content; closing after
  the switch restores focus to a still-connected appropriate opener, normally
  Settings, rather than an unmounted Transcript action.
- Derive the center text from current room state and the existing countdown
  behavior. Voting shows VOTE plus remaining time; an active question shows
  ANSWER plus remaining time. Interpretation and interpretation retry show
  PAUSED with the retained answer time, with existing errors/recovery elsewhere.
- Reuse server-owned deadlines, server-time offset and existing countdown
  formatting. Never start a new 15-second vote or 120-second answer window from
  mounting, rotating or reopening a drawer. Keep the existing urgent indication;
  color always accompanies a written phase label. A missing deadline must not
  fabricate remaining time.
- For no room or a waiting lobby, use Ready. When research planning is underway,
  use Mapping research…. When planning fails, show an appropriate retry-needed
  status. An opening-generation phase shows Preparing question…. A later
  generation after an accepted answer shows Reviewing answer…; after a timeout,
  use Reviewing missed turn…. Question-generation failure shows Retry needed.
  Completed defense shows Complete while the question/transcript continues to
  describe actual coaching generation or failure. These are interface statuses,
  not prewritten panelist dialogue or additional AI requests.
- Keep countdown semantics accessible without announcing every display tick.
  Phase/status changes may be announced politely; the rapidly updating timer
  should not continuously interrupt reading the question.
- Preserve the previous exchange while the next question is generated, exact
  grounded citations and extracted-text labels. Retain all four panelist and
  defender positions and the existing bottom dock and chosen-defender indication.
  The header change must not remount the room, composer or socket.
- Keep preview fixtures representative of the compact header. Preview-only
  presenter controls can live in Controls rather than add another mobile header
  row. Preview actions remain synthetic and must not initiate provider/AI calls.
- Extend existing navigation callbacks between the room, header and Controls
  only where needed for Transcript access. Introduce no room schema, WebSocket,
  account, payment or server protocol change and no new native capability.
- Work locally on the feature branch. Preserve existing uncommitted Account,
  upload and payment changes and unrelated files/deletions. This specification
  authorizes no remote publication or deployment; review the local implementation
  before a later user-requested push/deploy.

## Testing Decisions

- The primary automated seam is the existing whole-room React boundary with
  mocked room snapshots/socket/account responses. Exercise icon navigation,
  drawer switching, visible timer/status meaning, question progress and retained
  draft through the actual room rather than a replacement mobile mock page.
  Good tests assert user-visible behavior and accessible names, not private
  helpers, class names or CSS implementation details.
- Reuse existing room-header countdown/paused-time tests, whole-room draft and
  presenter checks, and shared drawer focus/Escape tests as prior art. Extend
  those where they clarify the public behavior; do not create a new server test
  seam or duplicate the entire defense state-machine suite for a header change.
- Cover voting, answering, paused interpretation, interpretation retry, opening
  generation, later answer review, timeout review, question retry, waiting lobby,
  research mapping/failure and completion/coaching states using mocked snapshots.
  Confirm that the correct status replaces the timer without inventing an answer
  or reporting unfinished coaching as ready.
- At the room boundary, open Settings, inspect room code/coverage, switch to
  Transcript, close, and open Account. Check host and guest navigation, meaningful
  labels, dialog focus containment, Escape and focus restoration across mode
  changes. Keep setup opening and completed-transcript behavior intact.
- Check answered/question progress for code and research defenses, including
  question numbers greater than eight. Preserve full questions, lead-ins,
  clarification history, exact citations, chosen defender and bottom dock.
- Browser verification uses the actual website at 320x568 and 390x844 portrait,
  667x375 landscape, a keyboard-sized 390x360 viewport and normal desktop, plus
  enlarged text. Verify one compact header row, timer centered relative to the
  viewport, at least 44-pixel icon targets, no clipped controls or horizontal
  page overflow, an internally scrollable reading area and reachable dock.
  CSS visibility and geometry require a real browser rather than jsdom alone.
- Rotate and resize during an active answer, navigate drawers and switch chat
  tabs; verify the same-turn draft remains. A mocked two-client smoke check
  verifies synchronized phase/deadline updates and answer submission through
  the existing socket. A geometry/viewport simulation is not physical-keyboard
  or installed-WebView evidence.
- Run the project's existing full offline Python and React gates and production
  build during implementation. AI and provider calls remain mocked. Source-only
  header changes do not establish live dialogue quality, provider checkout,
  hosted rollout or native installation.
- The user confirmed the existing whole-room React tests plus portrait/landscape
  browser checks as the testing boundaries for this header update. Installed
  Android/iOS checks are not an additional completion requirement for this
  website-only change. Existing broader mobile delivery prerequisites remain
  separate; these browser checks do not establish installed-device evidence.
- Present desktop/portrait/landscape screenshots and a working local preview
  before publication. Distinguish offline/mock browser, physical device, hosted
  and user-review evidence. Do not perform paid AI/provider calls just to verify
  the header.

## Out of Scope

- A new visual theme, separate mobile frontend, additional native navigation
  screen or replacement room design.
- Rebuilding or signing Android/iOS artifacts for this website-only layout
  change, app-store distribution and new native permissions or capabilities.
- Changing desktop layout, panelist/defender seat count, character design,
  question/citation presentation, bottom dock behavior or Streamlit appearance.
- Changing AI prompts, role order, research coverage policy, question limits,
  vote/answer durations, timeout/clarification policy, retry or reconnection rules.
- New account/payment features, clipboard tools, export formats, stored history,
  pricing, access changes, or dependency-vulnerability remediation.
- Modifying frozen main, pushing commits, triggering Render deployment, or
  treating design approval as visual review of an implementation.

## Further Notes

- The user approved all three interview recommendations: remove mobile header
  information boxes/title and keep information accessible in Controls or the
  question card; put Transcript inside Controls; show factual center statuses
  between timed phases. The same current theme and shared website remain the
  basis. Settings and Account are icon buttons; VOTE, ANSWER and PAUSED remain
  readable labels, not ambiguous timer-only numbers.
- This is a focused single-checkpoint specification. Implementation can proceed
  from this spec in one session; a ticket breakdown is useful only if the work
  grows beyond that scope. There is no unresolved visual-variant selection.
- The original broader mobile-app specification and delivery tickets remain
  separate. Their unresolved iOS signing, installed-device and provider checks
  are not silently completed or reopened by this header specification.
- Browser and WebView layouts come from the same deployed website. Layout
  updates appear after publication/deployment and page reload; this spec does
  not rebuild native apps or assume a Git push deploys the website.
- Ready-for-agent means this local Markdown spec is available for implementation,
  not that it is implemented, visually reviewed or deployed. No new discovery
  interview was conducted. The testing-expectation check is recorded separately.

## Implementation handoff — 2026-10-06

Implemented locally on the specified feature branch. User-confirmed review
baseline is the latest starting commit, 743d905. Existing whole-room tests now
cover Settings-to-Transcript focus/draft retention, truthful phase statuses,
server-owned and paused time, missing deadlines and guest research coverage.
Working-tree gate passes 219 offline Python tests (providers mocked), 184 React
tests and production build. Mocked portrait/landscape clients completed a fresh
four-turn defense with matching citations, votes, answers, reconnect and coaching.
Browser geometry, internal scrolling, icon targets, enlarged text and drawer
navigation passed. Physical-device and live-provider checks are not inferred.

Ready-for-human is for local visual review; no publication or deployment is
included. Independent Standards review found no hard breaches and one nonblocking simple
coverage-count duplication; Spec review found no actionable defects. Isolated
selected files pass 177 React tests and build, excluding unrelated pending edits.
Selective local commit is the handoff; publication remains a later request.

## Publication handoff — 2026-10-06

The user subsequently requested push and deployment. Feature release 23248cf
is Live at https://defense-simulator.onrender.com after one manual retry of a
failed automatic deployment. Health, exact production asset bytes and hosted
synthetic portrait/landscape/desktop navigation checks pass; see the review guide
and PROJECT_LOG.md. Main and unrelated local work remain unchanged. Status remains
ready-for-human for user visual review; no new live AI or installed-device evidence
is claimed. Documentation-only receipt skips another Render deployment.
