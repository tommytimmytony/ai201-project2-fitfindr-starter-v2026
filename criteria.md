# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I chose 4 of 5 because the query parser uses keyword matching and may not
recognize every phrasing. The run also depends on two model calls, so allowing
one miss accounts for model or service variability without making the target
easy.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
I chose 5 of 5 because checking whether the search returned an empty list is
deterministic Python code. This path stops before either model-dependent tool,
so the agent should make the same branching decision every time.

---

## 3. The selected item remains the same between tools

Given a query that matches at least one listing, the ID in
`session["selected_item"]` matches the ID of the item received by
`suggest_outfit` — in 5 of 5 tries.

**Why this target:**
I chose 5 of 5 because moving the selected item through the session is
deterministic and does not depend on model wording. A mismatch would mean the
loop passed stale or incorrect state to the next tool.

---

## 4. The fit card contains the required listing details

Given a matching query, the fit card contains the selected listing's title,
price, and platform and is between two and four sentences long — in 5 of 5
tries.

**Why this target:**
I chose 5 of 5 because these are required facts and format constraints, not
specific wording. The model may vary the caption's language while still
including the information a user needs every time.

---

## 5. Search results respect the maximum price

Given a matching query with a maximum price, every listing in
`session["search_results"]` has a price less than or equal to that maximum —
in 5 of 5 tries.

**Why this target:**
I chose 5 of 5 because price filtering is deterministic and directly affects
whether the recommendations respect the user's budget. Model variation cannot
justify returning an item above the requested maximum.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
