# Git workflow for 2 people, 2 machines, 2 GitHub accounts

## Once
1. Person A creates the GitHub repo `satyacheck` **at the event start** (commit timestamps are your proof that code was written during the event). Add this starter pack as the first commit, docs only.
2. A: Settings -> Collaborators -> invite B. B accepts the email invite.
3. On each machine, set your own identity so commits show the right author:
   `git config user.name "Your Name"` and `git config user.email "<your github email or noreply>"`
   Sign in with `gh auth login` (or SSH key / PAT). Then `git clone`.
4. Copy `.env.example` to `.env` (never committed). The signer (A) runs `python tools/gen_keys.py` and commits only the PUBLIC key file.

## Every task (the whole loop)
```
git pull --rebase origin main
# ... agent works, tests pass ...
./check.sh                      # or at least your task's pytest
git add -A && git commit -m "[T3] trust cohorts"
git pull --rebase origin main && git push
```
- Trunk-based: everyone pushes to `main` in small commits. No PR ceremony.
- Push at least every ~20 min, even `wip:` commits, so work survives a drained agent limit.
- Main auto-deploys, so only push green. If main breaks: `git revert <sha>` and push (never force-push).

## Why conflicts should be rare
File ownership is split in tasks/A.md and tasks/B.md. Shared files (`main.py`, `config.py`) are fully written in T0 so nobody edits them again. Status files are per person, so they never collide. If you need a change in the other person's file, put it under NEEDS in your status file or message them.

## If a rebase conflicts
`git status` -> fix the marked files -> `git add <files>` -> `git rebase --continue`. Lost? `git rebase --abort` and ask.

## Secrets
Never commit: `.env`, `*.db`, private keys, ADMIN_TOKEN, REPORTER_SALT, database URL. Set them in the host dashboard. The licence private key lives only on the signer's laptop, so the signer must be present to sign licences at the demo. Keep two licence files (5-minute and long) generated ahead of time on that laptop, or sign live there.

## Agent safety
Agents must not force-push, hard-reset, delete branches or stage ignored files (already in AGENTS.md).
