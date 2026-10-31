# Running several Antigravity agents at once (per person)
- One agent per task. Two agents must never edit the same file.
- Safe pairs for A: T1 (normalise) + T0 only after T0 is pushed. T3 can start once T2 is pushed.
- Safe pairs for B: T6 (licence) + T8a (frontend). T5 + T7 after A's T0.
- Give each agent prompts/kickoff.md with its own task id filled in. Nothing else needed.
- Use a stronger model for T3/T4 (trust), a cheaper/faster one for T8 (frontend) and T9 (docs), if Antigravity lets you pick per agent.
- Keep agent sessions short: one task, then stop. Do not keep a long-running agent thread open.
