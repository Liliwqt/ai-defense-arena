# Research practice prototype — local review

Date: 2026-10-17. Status: user selected **B — Speaker desk** on 2026-10-17. Production implementation remains pending.

Question: which layout makes live voice answering, manual Send and detailed post-defense coaching easiest to understand while retaining the app's research context?

This is a throwaway, development-only prototype on branch **prototype/research-practice**, captured in commit **f0d74a7**, based on feature source f15e756, isolated at `.local/worktrees/research-practice-prototype/`. The production feature branch remains unchanged. The [approved plan](DEFENSE_PRACTICE_IMPROVEMENTS_PLAN.md) remains the scope record; prototype code is not production implementation.

## Open and compare

Start with [B — Speaker desk](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=defense).

| Variant | Answer layout | Coaching layout |
| --- | --- | --- |
| [A — Room dock](http://127.0.0.1:8863/?prototype=research-practice&variant=A&stage=defense) | Panel, question and team above a wide answer dock. | Expandable question cards with a separate practice sidebar. |
| [B — Speaker desk](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=defense) | Research/question context beside a dedicated speaking workspace; stacks on phones. | Question selector and a focused coaching detail pane. |
| [C — Guided answer](http://127.0.0.1:8863/?prototype=research-practice&variant=C&stage=defense) | Numbered question/answer steps, with panel/team in expandable context. | A vertical learning sequence, with available cards expanded. |

Use the floating left/right arrows, or keyboard arrows outside text/select inputs. The variant is stored in the URL and survives reload; drafts/progress are memory-only and reset on reload. Switching variants without reload keeps the current demo draft.

The **Before**, **Defense** and **Coaching** buttons jump between simulated stages. **Go to answer** scrolls and focuses the mic or transcript, including on phones. The layout switcher has its own reserved strip and cannot cover product controls.

## Walkthrough

1. Open Before for the brief answer guide, voice recommendation and research-first modes.
2. Open Defense, press Go to answer, then Start demo mic. Synthetic words appear in the read-only field; no microphone permission is requested.
3. Press Send answer while the words are appearing. Finishing transcript appears, then one simulated acceptance. Silence never sends an answer.
4. Press Finish sample defense → Coaching. One synthetic closing appears, followed by progressive Results. The report uses three fixed synthetic turns; it does not evaluate text you entered.
5. Compare original wording, one captured filler, stronger supported wording, a practice task, simulated measurements, a typed answer with unavailable audio measures, and an unanswered question with a labeled scaffold.
6. Use Scenario and Reset demo to explore cap/deadline/probe/repeated-opening and failed-coaching cases. In B, choose Q2 to reach its failed-section retry. All financial recovery is simulated and changes no account balance.

Direct scenarios: [same-question reply](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=defense&case=probe), [voice cap](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=defense&case=cap), [deadline](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=defense&case=deadline), [failed coaching](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=results&case=failed), [repeated opening](http://127.0.0.1:8863/?prototype=research-practice&variant=B&stage=defense&case=repeat).

## Run again

From the shared repository root while this isolated worktree exists:

```bash
npm --prefix .local/worktrees/research-practice-prototype/game run prototype:practice
```

For a fresh checkout of the prototype branch, install its existing frontend dependencies and run `npm --prefix game run prototype:practice`. Port8863 must be free. The normal URL without `prototype=research-practice` still renders the existing app; the prototype entry and switcher are excluded from production builds.

## Evidence and limits

- TypeScript/Vite production build passed; existing PDF chunk-size warning only. Logs: `.local/research-practice-prototype/build-final.log` in the shared workspace. Production JS/CSS scan found no prototype UI/switcher markers or styles.
- Actual local Chromium, synthetic data: A/B/C at1440×960,390×844,844×390 all completed mic → finalizing Send → acceptance → one closing → progressive/full report, with no page errors or API/provider requests. Final responsive captures confirm no width overflow and an unobscured mic after Go to answer; Results width checks pass.
- Separate simulated interaction checks: interrupted capture retains unsent text without submitting/restarting; switching to typing clears voice; keyboard arrows inside typing do not change layouts; variant switch preserves the current draft and reload preserves the variant but clears draft; cap does not auto-send and allows typing; deadline during finalization prevents acceptance; probe reply remains Q1; repeated rejected opening is not displayed as an active question; retry changes its angle; failed-section retry retains the completed card without replaying closing; simulated credit return is once-only.
- Screenshots are local artifacts under `.scratch/research-practice-prototype/evidence/`, named `rp-final-{defense,answer,results}-{A,B,C}-{1440,390,844}.png`. Example: [phone answer controls](../.scratch/research-practice-prototype/evidence/rp-final-answer-B-390.png), [desktop speaker desk](../.scratch/research-practice-prototype/evidence/rp-final-defense-B-1440.png), [coaching cards](../.scratch/research-practice-prototype/evidence/rp-final-results-A-390.png).
- No new automated test suite was written for throwaway UI. No real speech recognition, audio measurement, persistence, credit return, native build/capture, paid provider call or hosted check is established. The user selected layout B; this is a layout decision, not verification of production behavior. All report text and measurements are labeled synthetic. Current source/pending files are preserved.

## Next handoff

The user selected **B — Speaker desk**: research/question context beside the speaking workspace, stacked on phones, and a question selector with focused coaching detail. The selected layout is captured in verdict commit **a3046c4** on **prototype/research-practice**, with source **f0d74a7**. The [local specification](../.scratch/defense-practice/spec.md) incorporates this decision and is ready-for-agent; next is To Tickets. Rewrite validated behavior under normal implementation/tests; do not merge the throwaway variants or switcher into production.
