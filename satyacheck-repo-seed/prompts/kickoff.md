You are an agent on SatyaCheck. I am Person <A|B>. Your task is <T#>.
Read ONLY: AGENTS.md, then my entry <T#> in tasks/<A|B>.md, then the docs/ files that entry names, then the last 15 lines of status/<A|B>.md. Do not read other docs and do not explore the repo.
Do only that task and only touch the files it lists. Follow AGENTS.md rules. When the test passes: tick the box, add a short status entry, then
git add -A && git commit -m "[<T#>] ..." && git pull --rebase origin main && git push
If you run low on budget, commit a `wip:` and write LEFT OFF AT in the status file first.
