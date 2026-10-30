---
name: stage
description: Run one stage of the NerdHealth plan end to end — plan, tests first, implement, review, close. Use when Nicolas says "/stage N", "start stage N", "continue the stage", or "close stage N".
---

# Run a stage

Argument: the stage number `N`. If none is given, take the stage that is `in_progress` in
`requirements.yaml`, or else the first `planned` one, and confirm it with Nicolas.

Every step ends with a check. Do not move to the next step until it passes.

## 0. Preconditions

- Read `CLAUDE.md`, `docs/PROGRESS.md`, and the Stage N section of `docs/PLAN.md`, plus any
  section of `docs/PLAN.md` it refers to (§3 for the requirements, §6 for tests and CI).
- Every earlier stage is `done` in `requirements.yaml`. If not, stop and say which.
- The working tree is clean and `make check` passes on `main`.
- **Resuming?** If Stage N is already `in_progress`, read `docs/PROGRESS.md` for where it
  stopped and continue from that step instead of starting over.

## 1. Branch and open the stage

```bash
git switch -c stage/N-<short-name>
```

Set Stage N to `in_progress` in `requirements.yaml`. Commit: `chore(stage-N): open stage`.

## 2. Plan — then wait

Write the plan in plan mode and present it. It must contain:

- **Every requirement** the stage delivers (from `requirements.yaml`), and for each one the
  test(s) that will verify it, by name. For `manual` requirements, the evidence that will be
  recorded.
- **Every "Done when" criterion** from `docs/PLAN.md`, and how it will be checked.
- What is **stretch** and will be cut first if the stage runs over its estimate.
- Any place where the spec looks wrong or underspecified. Do not resolve it yourself.

**Stop and wait for Nicolas to approve the plan.** Nothing is written before that.

## 3. Tests first

- Write the tests from the plan, each tagged `@pytest.mark.req(...)`.
- Run them and confirm they **fail for the right reason** (missing behaviour, not an import
  error or a typo). Report the failures briefly.
- Commit: `test(stage-N): ...`.

## 4. Implement

- Small commits, Conventional Commits with `stage-N` as scope.
- After each meaningful change, `make test`. Before moving on, `make check`.
- If a test seems wrong, **stop and say so**. Never edit a test to match the code without
  saying why.
- If the stage reaches 1.5× its estimate in `docs/PLAN.md`, cut the stretch items and tell
  Nicolas.

## 5. Review

Run the `stage-reviewer` agent with the stage number. It has no context from this session,
on purpose.

- `CHANGES REQUIRED`: fix every finding, commit, run the reviewer again.
- A finding you believe is wrong: do not silently ignore it. Record it in
  `docs/PROGRESS.md` with the reason, and tell Nicolas.
- Loop until `PASS`.

## 6. Close

- Fill `evidence` for every `manual` requirement of the stage.
- Set Stage N to `done` in `requirements.yaml`.
- `make check`. **It must pass with the stage marked done**: that is the proof that every
  requirement is verified. If it fails, the stage is not done; go back to step 4.
- Update `docs/PROGRESS.md` (see its format): what was delivered, decisions and why,
  shortfalls, what the reviewer said.
- Add any new commands to the Commands section of `CLAUDE.md`.
- Commit: `docs(stage-N): close stage`.

## 7. Hand over — then stop

Ask before pushing. When Nicolas agrees:

```bash
git push -u origin stage/N-<short-name>
gh pr create --title "Stage N — <name>" --body "<summary, requirements verified, shortfalls>"
```

Report in Spanish: what was delivered, what fell short, the PR link.
**Do not start Stage N+1.**

## If the session ends mid-stage

Before stopping, write in `docs/PROGRESS.md` exactly which step of this skill you are on and
what is left, and commit it, so the next session can resume from step 0.
