"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "suggest_outfit_input": None,  # exact item passed into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """Extract the description, optional size, and optional maximum price."""
    working = query.strip()

    price_match = re.search(
        r"\b(?:under|below|less\s+than|up\s+to|max(?:imum)?(?:\s+of)?)"
        r"\s*\$?\s*(\d+(?:\.\d+)?)",
        working,
        flags=re.IGNORECASE,
    )
    max_price = float(price_match.group(1)) if price_match else None
    if price_match:
        working = working[:price_match.start()] + working[price_match.end():]

    size_match = re.search(
        r"\b(?:in\s+)?size\s+"
        r"(one\s+size|us\s+\d+(?:\.\d+)?|w\d+|[xsml]+(?:/[xsml]+)?|\d+(?:\.\d+)?)"
        r"\b",
        working,
        flags=re.IGNORECASE,
    )
    size = size_match.group(1).upper() if size_match else None
    if size_match:
        working = working[:size_match.start()] + working[size_match.end():]

    description = re.sub(
        r"^(?:i(?:'m| am)?\s+)?(?:am\s+)?(?:looking\s+for|want|need)\s+",
        "",
        working.strip(),
        flags=re.IGNORECASE,
    )
    description = re.sub(r"^[,\s]*(?:a|an|the)\s+", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\s+", " ", description).strip(" ,.-")

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    The loop parses the query, searches the listings, and branches on the
    stored search result. An empty result sets an actionable error and stops.
    A successful result moves through selected_item, suggest_outfit, and
    create_fit_card, with every input and result read from session state.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    next_step = "parse_query"
    iteration_count = 0

    while next_step is not None:
        iteration_count += 1
        trace.check_iterations(iteration_count)

        if next_step == "parse_query":
            session["parsed"] = _parse_query(session["query"])
            next_step = "search_listings"
            continue

        if next_step == "search_listings":
            parsed = session["parsed"]
            session["search_results"] = search_listings(
                description=parsed["description"],
                size=parsed["size"],
                max_price=parsed["max_price"],
            )

            if not session["search_results"]:
                session["error"] = (
                    "I couldn't find a listing matching those filters. Try "
                    "broader item words, remove or change the size, or raise "
                    "the maximum price."
                )
                return session

            session["selected_item"] = session["search_results"][0]
            next_step = "suggest_outfit"
            continue

        if next_step == "suggest_outfit":
            session["suggest_outfit_input"] = session["selected_item"]
            session["outfit_suggestion"] = suggest_outfit(
                session["suggest_outfit_input"],
                session["wardrobe"],
            )
            next_step = "create_fit_card"
            continue

        if next_step == "create_fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"],
                session["selected_item"],
            )
            next_step = None
            continue

        raise RuntimeError(f"Unknown planning step: {next_step}")

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
