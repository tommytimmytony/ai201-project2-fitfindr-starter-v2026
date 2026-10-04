"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


_SEARCH_STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "can",
    "carry",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "get",
    "has",
    "have",
    "how",
    "i",
    "in",
    "looking",
    "me",
    "of",
    "please",
    "sell",
    "selling",
    "shop",
    "show",
    "stock",
    "store",
    "the",
    "to",
    "want",
    "what",
    "when",
    "where",
    "why",
    "with",
    "you",
    "your",
}


def _normalize_word(word: str) -> str:
    """Normalize common English plurals so jackets matches jacket."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("sses", "shes", "ches", "xes", "zes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "is", "us")):
        return word[:-1]
    return word


def _words(value: str) -> set[str]:
    """Return lowercase search tokens without punctuation or filler words."""
    return {
        _normalize_word(word)
        for word in re.findall(r"[a-z0-9]+", value.lower())
        if word not in _SEARCH_STOP_WORDS
    }


def _size_matches(requested_size: str, listing_size: str) -> bool:
    """Match complete size tokens so S does not match US and L does not match XL."""
    requested_tokens = set(re.findall(r"[A-Z]+|\d+(?:\.\d+)?", requested_size.upper()))
    listing_tokens = set(re.findall(r"[A-Z]+|\d+(?:\.\d+)?", listing_size.upper()))
    return bool(requested_tokens) and requested_tokens.issubset(listing_tokens)


def _listing_text(listing: dict) -> str:
    """Combine the searchable listing fields into one string."""
    values = [
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        listing.get("condition", ""),
        listing.get("brand") or "",
        listing.get("platform", ""),
        *listing.get("style_tags", []),
        *listing.get("colors", []),
    ]
    return " ".join(str(value) for value in values)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    query_words = _words(description)
    if not query_words:
        return []

    matches = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, listing["size"]):
            continue

        title_words = _words(listing.get("title", ""))
        tag_words = _words(" ".join(listing.get("style_tags", [])))
        other_words = _words(_listing_text(listing))

        score = (
            3 * len(query_words & title_words)
            + 2 * len(query_words & tag_words)
            + len(query_words & other_words)
        )
        if score:
            matches.append((score, listing))

    matches.sort(key=lambda match: (-match[0], match[1]["price"], match[1]["id"]))
    return [listing for _, listing in matches[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    wardrobe_items = wardrobe.get("items", [])
    item_details = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'not listed'}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'not listed'}\n"
        f"Size: {new_item.get('size', 'not listed')}\n"
        f"Price: ${new_item.get('price', 0):.2f}"
    )

    if wardrobe_items:
        wardrobe_lines = []
        for item in wardrobe_items:
            wardrobe_lines.append(
                f"- {item.get('name', 'Unnamed item')} "
                f"({item.get('category', 'unknown category')}; "
                f"colors: {', '.join(item.get('colors', [])) or 'not listed'}; "
                f"style: {', '.join(item.get('style_tags', [])) or 'not listed'}"
                f"{'; notes: ' + str(item['notes']) if item.get('notes') else ''})"
            )

        prompt = (
            "Suggest one or two complete outfits for the new item below. "
            "Use and name specific pieces from the user's wardrobe. Explain "
            "briefly why the pieces work together.\n\n"
            f"NEW ITEM\n{item_details}\n\n"
            "USER'S WARDROBE\n"
            + "\n".join(wardrobe_lines)
        )
    else:
        prompt = (
            "The user has not added any wardrobe items yet. Suggest one or two "
            "general ways to style the new item below. Name the types of tops, "
            "bottoms, shoes, outerwear, or accessories they could pair with it.\n\n"
            f"NEW ITEM\n{item_details}"
        )

    response = generate(
        prompt,
        system=(
            "You are a practical thrift-fashion stylist. Give concise, specific "
            "outfit advice and do not invent items in the user's wardrobe."
        ),
    ).strip()
    if not response:
        raise RuntimeError("The model returned an empty outfit suggestion.")
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit.strip():
        return "A fit card cannot be created until an outfit suggestion is available."

    title = new_item.get("title", "Unknown item")
    price = new_item.get("price", 0)
    platform = new_item.get("platform", "unknown platform")
    prompt = (
        "Write a social-media-style fit card using the details below.\n\n"
        "Requirements:\n"
        "- Write exactly two to four sentences.\n"
        f'- Include the exact item title: "{title}".\n'
        f"- Include the exact price: ${price:.2f}.\n"
        f'- Include the exact platform name: "{platform}".\n'
        "- Mention the outfit's specific styling and overall vibe.\n"
        "- Sound natural rather than like a product listing.\n"
        "- Do not add a heading or bullet points.\n"
        "- Do not claim the user owns, purchased, or has worn the item.\n"
        "- Do not invent scarcity or urgency.\n"
        "- Describe it as an item the user could buy and style.\n\n"
        f"OUTFIT SUGGESTION\n{outfit}"
    )

    response = generate(
        prompt,
        system=(
            "You write concise thrift-fashion captions. Follow every requested "
            "fact and length constraint while allowing the wording to vary."
        ),
    ).strip()
    if not response:
        raise RuntimeError("The model returned an empty fit card.")
    return response
