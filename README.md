# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr helps a user search a collection of secondhand clothing listings
using a description, optional size, and maximum price. It selects the most
relevant result and suggests outfits that combine the new item with pieces
from the user's wardrobe. It then creates a short fit-card caption containing
the selected item's title, price, platform, and styling vibe. If no listing
matches, the agent stops before the model-backed tools and tells the user which
filters they can change.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the listings data for items that match the user's description and optional size and maximum price, then orders the matches from most relevant to least relevant.
- **Inputs:** `description` (`str`) contains the search keywords; `size` (`str | None`) optionally limits results to compatible sizes using case-insensitive size-token matching; `max_price` (`float | None`) optionally limits results to listings whose price is less than or equal to the given amount.
- **Returns:** A `list[dict]` containing at most `config.SEARCH_RESULT_LIMIT` listing dictionaries, ordered by keyword-match score. Each dictionary contains `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** Returns an empty list (`[]`), never `None` and never an error string.

### `suggest_outfit`

- **What it does:** Uses the model to suggest one or two ways to style a selected listing with pieces from the user's wardrobe.
- **Inputs:** `new_item` (`dict`) is one listing dictionary selected from the search results; `wardrobe` (`dict`) contains an `items` list of wardrobe-item dictionaries.
- **Returns:** A non-empty `str` describing one or two outfits. When wardrobe items are available, the suggestions name specific pieces the user owns.
- **When it has nothing:** If `wardrobe["items"]` is empty, returns a non-empty string containing general styling advice for `new_item` instead of failing.

### `create_fit_card`

- **What it does:** Uses the model to turn an outfit suggestion and selected listing into a short, post-style caption.
- **Inputs:** `outfit` (`str`) is the suggestion returned by `suggest_outfit`; `new_item` (`dict`) is the same selected listing passed to `suggest_outfit`.
- **Returns:** A non-empty `str` containing a two-to-four-sentence caption that mentions the item, its price, its platform, and the outfit's vibe.
- **When it has nothing:** If `outfit` is empty or contains only whitespace, returns a descriptive string explaining that a fit card cannot be created without an outfit suggestion.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put an actionable message in `session["error"]` telling the user to broaden the description, remove the size filter, or raise the maximum price, then stop and return the session. Otherwise, put the first search result in `session["selected_item"]` and continue to `suggest_outfit`, followed by `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions and string cleanup extract a maximum price from phrases such as `under $30` and a size from phrases such as `size M` or `in size M`. The remaining text becomes the description used for keyword matching.

**What moves through the session:** The original text starts in `session["query"]`. The extracted `description`, `size`, and `max_price` go into `session["parsed"]`. Search output goes into `session["search_results"]`; its first item goes into `session["selected_item"]`. The exact item passed to the next tool is recorded in `session["suggest_outfit_input"]`, and that item plus `session["wardrobe"]` produce `session["outfit_suggestion"]`. Finally, the stored outfit suggestion and the same stored selected item produce `session["fit_card"]`. If search returns no results, `session["error"]` is set and the later fields remain `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Vintage Band Tee — Faded Grey — $19.0 on depop

  Outfit:   **Outfit 1: 90s Grunge Streetwear**
*   **New Item:** Vintage Band Tee (Faded Grey)
*   **Bottoms:** Baggy straight-leg jeans (dark wash)
*   **Outerwear:** Vintage black denim jacket
*   **Shoes:** Black combat boots
*   **Accessories:** Black crossbody bag

**Why it works:** The faded grey band tee and baggy dark jeans build an
effortless, authentic 90s silhouette. Layering the slightly cropped black
denim jacket adds subtle texture and dimension against the charcoal tee,
while the black combat boots anchor the grunge aesthetic.

  Fit card: I'm living for this effortless 90s grunge streetwear vibe,
anchored by the Vintage Band Tee — Faded Grey layered under a black denim
jacket. Tucked into dark baggy straight-leg jeans with combat boots, it’s the
ultimate slouchy silhouette for only $19.00. Snag this piece and the rest of
the look over on my depop shop before it sells out!

2 model calls this session
```

**Empty-search branch**

```
$ python app.py ask 'designer ballgown size XXS under $5'

  I couldn't find a listing matching those filters. Try broader item words,
  remove or change the size, or raise the maximum price.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print([(x['title'], x['size'], x['price']) for x in search_listings('graphic tee', max_price=30)])"
[('Graphic Tee — 2003 Tour Bootleg Style', 'L', 24.0), ('Y2K Baby Tee — Butterfly Print', 'S/M', 18.0), ('Vintage Band Tee — Faded Grey', 'L', 19.0), ('Vintage Graphic Hoodie — Faded Black', 'L', 26.0), ('Mesh Long-Sleeve Top — Black', 'S/M', 15.0), ('Low-Rise Cargo Pants — Khaki', 'W29', 27.0)]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[5], get_example_wardrobe()))"
**Outfit 1: 90s Streetwear Grunge**
* **Top:** Graphic Tee — 2003 Tour Bootleg Style
* **Bottoms:** Baggy straight-leg jeans (dark wash)
* **Outerwear:** Black cropped zip hoodie (worn open or layered over)
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Why it works:** The bootleg band tee naturally leans into streetwear and
grunge. Pairing it with dark wash baggy jeans creates an effortless,
proportions-conscious silhouette. Layering the black cropped zip hoodie keeps
the color palette cohesive while adding texture, and the chunky white sneakers
tie in the bright elements of the graphic tee.

***

**Outfit 2: Edgy Contrast**
* **Top:** Graphic Tee — 2003 Tour Bootleg Style
* **Outerwear:** Vintage black denim jacket
* **Bottoms:** Wide-leg khaki trousers
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt, Black crossbody bag

**Why it works:** This outfit balances the casual, rebellious vibe of the
graphic tee with tailored structure. Tucking the tee in with the brown leather
belt defines the waist against the relaxed, wide-leg khaki trousers. Topping it
with the vintage black denim jacket and grounding the look with black combat
boots gives the earth-toned trousers a tough, grunge-ready edge.
```

```
$ python -c "import config; config.CACHE_ENABLED=False; from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[5]; outfit='Baggy jeans, a black cropped hoodie, and chunky white sneakers.'; [print('Run', i+1, create_fit_card(outfit, item)) for i in range(3)]"
Run 1: I've been living in this effortless streetwear look, centered around my Graphic Tee — 2003 Tour Bootleg Style paired with baggy jeans, a black cropped hoodie, and chunky white sneakers. The vibe is totally nostalgic and relaxed, perfect for everyday errands or hanging out with friends. You can grab this exact top on depop right now for just $24.00.
Run 2: I've been living in this vintage-inspired Graphic Tee — 2003 Tour Bootleg Style for the ultimate effortless grunge look. Paired with baggy jeans, a black cropped hoodie, and chunky white sneakers, it gives off such an authentic, laid-back 90s skater vibe. Grab this piece now for $24.00 over on my depop before it finds a new home.
Run 3: Styled this vintage look with baggy jeans, a black cropped hoodie, and chunky white sneakers for the ultimate cozy streetwear vibe. The centerpiece is the Graphic Tee — 2003 Tour Bootleg Style, adding that perfect worn-in edge to the fit. Grab this piece right now on depop for just $24.00 before it's gone.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Copilot to review my `search_listings` contract
  and explain how size matching could be tested against the real dataset.
- *What came back:* It pointed out that a plain substring check would make
  `"S"` match `"US 9"` and `"L"` match `"XL"`, even though those are different
  sizes.
- *What I changed:* I used complete size tokens and required the requested
  tokens to exist in the listing size. I also tested that a search for
  sneakers in size `S` returns an empty list rather than shoe sizes containing
  the letter `S`.

**Moment 2**

- *What I asked for:* I asked Copilot how to make the selected-item handoff
  visible enough to test my state acceptance criterion.
- *What came back:* It suggested recording the exact item used as the
  `suggest_outfit` input instead of relying on a temporary local variable.
- *What I changed:* I added `session["suggest_outfit_input"]`, called
  `suggest_outfit` using that stored value, and checked that its ID matched
  `session["selected_item"]["id"]`. I also kept the empty-search branch before
  that assignment so no item reaches the model when search returns `[]`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
