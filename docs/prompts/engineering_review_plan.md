# Review this plan thoroughly before making any code changes.

For every issue or recommendation, explain the concrete tradeoffs, give me an opinionated recommendation, and ask for my input before assuming a direction.

---

## My engineering preferences (use these to guide your recommendations):

* DRY is important-flag repetition aggressively.
* Well-tested code is non-negotiable I'd rather have too man tests than too few.
* I want code that's "engineered enough - not under-engineered (tragile, hacky) and not over-engineered (premature abstraction, unnecessary complexity lerr on the side of handling more edge cases, not fewer; thoughtfulness> speed.
* Bias toward explicit over clever.

---

## 1. Architecture review

Evaluate:

* Overall system design and component boundaries.Dependency graph and coupling concerns.Data flow patterns and potential bottlenecks.
* Scaling characteristics and single points of failure.
* Security architecture (auth, data access, API boundaries).

---

## 2. Code quality review

Evaluate:

* Code organization and module structure.
* DRY violations be aggressive here.
* Error handling patterns and missing edge cases (call these out explicitly).
* Technical deht hotenots
* Areas that are over-engineered or under-engineered relative to my preferences.

---

## 3. Test review

Evaluate:

* Test coverage gaps (unit, integration, e2e).Test quality and assertion strength.
* Missing edge case coverage-be thorough.
* Untested failure modes and error naths.

---

## 1 Darformance raviam

Evaluate:

* N+1 queries and database access patterns.
* Memorv-lisaee concerns
* Caching opportunities.
* Slow or high-complexity code paths.

---

## For each issue you find

For every specitic issue (bug, smell, design concern, or risk):

* Describe the problem concretely, with file and line references.
* Present 2-3 options, including "do nothing" where that's reasonable.
* Por sent 2-3 options, includine no nothing where that's reason other code, and maintenance burden.
* Give me your recommended option and why, mapped to my preferences above.
* Then explicitly ask whether I agree or want to choose a different direction before proceeding.

---

## Workflow and interaction

* Do not assume my priorities on timeline or seale
* After each section, pause and ask for my feedback before moving on.

---

## BEFORE YOU START:

Ack if want one of two antione

### BIG CHANGE

Work throuch thic intaractive ane coction at atimo Architecture ade malty Tact Partarmanca With at mact tan iccuac in addl section.

### 2/ SMALL CHANGE:

Work through interactively ONE question per review section

---

## FOR EACH STAGE OF REVIEW:

Output the explanation and pros and cons of each stage's questions AND vour opinionated recommendation and why. and then us AskUserQuestion.

Also NUMBER issues and then give LETTERS for options and when using AskUserQuestion make sure each option clearly labels the issue NUMBER and option LETTER so the user doesn't get confused.

Make the recommended option always the 1st option

