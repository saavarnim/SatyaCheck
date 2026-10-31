# SatyaCheck: agent entry (this is the ONLY file everyone reads)
Stack: FastAPI + SQLAlchemy + plain HTML/JS served by FastAPI. No Node, no Docker.

## The loop
1. Read this file, your task entry in `tasks/<A|B>.md`, and the ONE doc that entry names. Nothing else. Do not explore or grep the repo.
2. Touch only the files your task lists.
3. Start writing code immediately. After EACH file or function: run only that test, then
   `git add -A && git commit -m "[ID] what" && git pull --rebase origin main && git push`
4. After every push, append ONE line to `status/<you>.md`:
   `[ID] done|wip | LEFT OFF AT: <next small step>`
5. Ambiguous? Pick the simplest option, add `ASSUMED: ...` to status, continue.
6. Never: force-push, `reset --hard`, delete branches, stage `.env` / `*.db` / keys.

## Read ONLY if your task needs it
- `docs/rules.md`: privacy and API rules. Read it if you write any response, log line or stored field.
- `docs/map.md`: one line per repo file. Read it only if you cannot find a file.
