# Partial coaching visibility does not settle the defense run

Status: accepted design, confirmed with the consolidated plan on 2026-10-17; implemented locally in ticket 06 (2026-10-18); user visual and actual-provider review pending.

Every-answer coaching can finish in sections, so show the optional closing once after the overview and expose ready cards/progress in Results while other required sections continue. Keep the full report and financial run incomplete until all required coaching succeeds; preserve finished sections, free failed-section retries and existing eligible end-unavailable credit returns. This deliberately separates visible Results from successful financial completion: retries must not replay the closing, and late work after recovery or restart cannot settle twice, reverse a return or overwrite a newer run.
