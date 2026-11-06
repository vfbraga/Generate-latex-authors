#!/usr/bin/env python3
"""
Generate the author list + affiliations in LaTeX (and the mailing list) for a paper.
Python translation of generate_latex_authors.pro; the data live in authors_db.py.

Usage from Python:
    from generate_latex_authors import generate_latex_authors, mailing_list
    authors = ["braga", "stetson", "bono", "dallora"]      # in the order of the paper
    print(generate_latex_authors(authors, style="mnras"))
    print(mailing_list(authors))

Usage from the command line:
    python generate_latex_authors.py braga stetson bono --style mnras   # emails (one per line) + LaTeX
    python generate_latex_authors.py braga stetson bono --style mnras --no-emails
    python generate_latex_authors.py braga stetson bono --emails        # emails only
    python generate_latex_authors.py --all --style aastex63
    python generate_latex_authors.py braga borg -s aastex701 -c braga --no-emails
    python generate_latex_authors.py --list
    python generate_latex_authors.py --check

Styles (in parentheses, the number used by the IDL macro):
    apj_old (0), aa (1), mnras (2), arxiv (3), aastex63 (4), aastex701 (no number)

An author can be referred to by database key ("braga"), by alias ("laurainno") or
by name ("V.~F.~Braga" / "V.F. Braga"), case-insensitively.

Affiliation numbering (as in the IDL macro): institutes are numbered 1, 2, ... in
the order in which they first appear when scanning the author list; for each
author the numbers are printed in increasing order.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys

from authors_db import AUTHORS, INSTITUTES

# --------------------------------------------------------------------------- author lookup


def _norm(s: str) -> str:
    return re.sub(r"[\s~]+", " ", s).strip().lower()


def _build_lookup() -> dict[str, str]:
    lookup = {}
    for key, a in AUTHORS.items():
        for alias in (key, *a.get("aliases", ()), a["name"], a["name_arxiv"]):
            lookup[_norm(alias)] = key
    return lookup


_LOOKUP = _build_lookup()


def get_authors(queries) -> list[dict]:
    """List of keys/aliases/names -> list of author records (same order)."""
    out, unknown = [], []
    for q in queries:
        key = _LOOKUP.get(_norm(q))
        if key is None:
            unknown.append(q)
        else:
            out.append(AUTHORS[key])
    if unknown:
        lines = [f"ERROR: {len(unknown)} unrecognized keyword{'' if len(unknown) == 1 else 's'}:"]
        for q in unknown:
            close = difflib.get_close_matches(_norm(q), list(_LOOKUP), n=3)
            lines.append(f"  - {q!r}" + (f"  (did you mean: {', '.join(close)}?)" if close else ""))
        raise KeyError("\n".join(lines))
    return out


# --------------------------------------------------------------------------- affiliation numbering


def number_institutes(authors: list[dict]):
    """Return (order, number): institutes in order of first appearance, and key -> 1, 2, ..."""
    order: list[str] = []
    for a in authors:
        for inst in a["affiliations"]:
            if inst not in order:
                order.append(inst)
    return order, {inst: i for i, inst in enumerate(order, 1)}


def _nums(a: dict, number: dict[str, int]) -> str:
    return ",".join(str(k) for k in sorted(number[i] for i in a["affiliations"]))


def _full(inst: str) -> str:
    return INSTITUTES[inst]["full"]


# --------------------------------------------------------------------------- styles


def _apj_old(authors, order, number):
    n = len(authors)
    lines = [r"\author{"]
    for i, a in enumerate(authors):
        lines.append(a["name"] + r"\altaffilmark{" + _nums(a, number) + "}" + ("" if i == n - 1 else ","))
    lines.append("}")
    for k, inst in enumerate(order, 1):
        lines.append(r"\altaffiltext{" + str(k) + "}{" + _full(inst) + "}")
    return lines


def _aa(authors, order, number):
    lines = [r"\author{"]
    for i, a in enumerate(authors):
        lines.append(("" if i == 0 else r"\and ") + a["name"] + r"\inst{" + _nums(a, number) + "}")
    lines += ["}", r"\institute{"]
    for i, inst in enumerate(order):
        # as in the original IDL macro: the last institute ends with "\\"
        lines.append(("" if i == 0 else r"\and ") + _full(inst) + (r"\\" if i == len(order) - 1 else ""))
    lines.append("}")
    return lines


def _mnras(authors, order, number):
    n = len(authors)
    first = authors[0]
    lines = [r"\author[" + first["name"] + (" et al." if n > 1 else "") + "]{"]
    for i, a in enumerate(authors):
        prefix = "" if i == 0 else ("and " if i == n - 1 else ", ")
        line = prefix + a["name"] + "$^{" + _nums(a, number) + "}$"
        if i == 0:
            line += r"\thanks{E-mail: " + a["email"] + "}"
        lines.append(line)
    lines.append(r"\\")
    for k, inst in enumerate(order, 1):
        lines.append("$^{" + str(k) + "}$" + _full(inst) + ("" if k == len(order) else r"\\"))
    lines.append("}")
    return lines


def _arxiv(authors, order, number):
    names = ", ".join(f"{a['name_arxiv']} ({_nums(a, number)})" for a in authors)
    affs = ", ".join(f"({k}) {INSTITUTES[inst]['short']}" for k, inst in enumerate(order, 1))
    return [names, "(" + affs + ")"]


def _aastex63(authors, order, number):
    lines = []
    for a in authors:
        orcid = a.get("orcid")
        lines.append((r"\author[" + orcid + "]{" if orcid else r"\author{") + a["name"] + "}")
        for inst in a["affiliations"]:  # here the order of the list matters, not the numeric one
            lines.append(r"\affiliation{" + _full(inst) + "}")
    return lines


def _aastex701(authors, order, number, corresponding=None):
    """AASTeX 7.0.1: \\author[orcid=...], \\affiliation, \\email. The email is shown
    (\\email[show]) only for the corresponding author, if one is given."""
    lines = []
    if corresponding is not None:
        lines.append(r"\correspondingauthor{" + corresponding["name"] + "}")
    for i, a in enumerate(authors):
        if i > 0:
            lines.append("")
        orcid = a.get("orcid")
        lines.append((r"\author[orcid=" + orcid + "]{" if orcid else r"\author{") + a["name"] + "}")
        for inst in a["affiliations"]:  # order of the list, as in aastex63
            lines.append(r"\affiliation{" + _full(inst) + "}")
        if a.get("email"):
            show = "[show]" if a is corresponding else ""
            lines.append(r"\email" + show + "{" + a["email"] + "}")
    return lines


STYLES = {
    "apj_old": _apj_old,
    "aa": _aa,
    "mnras": _mnras,
    "arxiv": _arxiv,
    "aastex63": _aastex63,
    "aastex701": _aastex701,
}
STYLE_NUMBERS = {0: "apj_old", 1: "aa", 2: "mnras", 3: "arxiv", 4: "aastex63"}
STYLE_HINTS = {
    "mnras": r"If there are many authors, use \newauthor to start a new line.",
}


def generate_latex_authors(authors, style="mnras", corresponding=None) -> str:
    """Authors and affiliations in the requested style (name, or number of the IDL macro).

    corresponding: key/alias/name of the corresponding author (must be in the author
    list); currently used only by the aastex701 style.
    """
    style = STYLE_NUMBERS.get(style, style)
    if style not in STYLES:
        raise ValueError(f"Invalid style {style!r}. Choose among {sorted(STYLES)}")
    if corresponding is not None and style != "aastex701":
        raise ValueError("ERROR: the corresponding author is only supported by the aastex701 style")
    # single lookup, so wrong keywords (authors and corresponding author) are reported together
    recs = get_authors(list(authors) + ([corresponding] if corresponding is not None else []))
    corr = recs.pop() if corresponding is not None else None
    if corr is not None and not any(corr is a for a in recs):
        raise ValueError(f"ERROR: the corresponding author {corresponding!r} is not in the author list")
    order, number = number_institutes(recs)
    kwargs = {"corresponding": corr} if style == "aastex701" else {}
    return "\n".join(STYLES[style](recs, order, number, **kwargs))


def mailing_list(authors, sep="\n") -> str:
    """Authors' emails in the given order, one per line (or separated by `sep`)."""
    return sep.join(a["email"] for a in get_authors(authors) if a.get("email"))


# --------------------------------------------------------------------------- database checks

_EMAIL_RE = re.compile(r"^[^@\s]+@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}$")
_ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


def check_database() -> list[str]:
    """Consistency checks. Lines starting with "(info)" are not errors."""
    problems = []
    used = set()
    seen_orcid: dict[str, str] = {}
    for key, a in AUTHORS.items():
        if not a["affiliations"]:
            problems.append(f"{key}: no affiliation")
        for inst in a["affiliations"]:
            used.add(inst)
            if inst not in INSTITUTES:
                problems.append(f"{key}: unknown institute {inst!r}")
        if not a.get("email"):
            problems.append(f"{key}: missing email")
        elif not _EMAIL_RE.match(a["email"]):
            problems.append(f"{key}: suspicious email {a['email']!r}")
        o = a.get("orcid")
        if o:
            if not _ORCID_RE.match(o):
                problems.append(f"{key}: invalid ORCID {o!r}")
            if o in seen_orcid:
                problems.append(f"{key}: same ORCID as {seen_orcid[o]}")
            seen_orcid[o] = key
        if re.search(r"~\.|\.\.", a["name"]):
            problems.append(f"{key}: suspicious name {a['name']!r}")
    for inst in INSTITUTES:
        if inst not in used:
            problems.append(f"(info) institute not used by any author: {inst}")
    return problems


# --------------------------------------------------------------------------- command line


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("authors", nargs="*", help="keys/aliases/names, in the order of the paper")
    ap.add_argument("--style", "-s", default="mnras",
                    help="apj_old | aa | mnras | arxiv | aastex63 | aastex701 (or 0-4)")
    ap.add_argument("--corresponding", "-c", default=None, metavar="AUTHOR",
                    help="corresponding author (aastex701 only): the only one whose email is shown")
    ap.add_argument("--emails", "-e", action="store_true", help="print only the mailing list")
    ap.add_argument("--no-emails", action="store_true", help="do not print the mailing list before the LaTeX")
    ap.add_argument("--all", action="store_true", help="use all the authors in the database")
    ap.add_argument("--list", action="store_true", help="list the author keys")
    ap.add_argument("--check", action="store_true",
                    help="check the database consistency (exit code 1 if there are errors)")
    a = ap.parse_args(argv)

    if a.list:
        for key, rec in AUTHORS.items():
            print(f"{key:20s} {rec['name_arxiv']}")
        return 0
    if a.check:
        probs = check_database()
        print("\n".join(probs) if probs else "Database OK")
        return 1 if any(not p.startswith("(info)") for p in probs) else 0

    authors = list(AUTHORS) if a.all else a.authors
    if not authors:
        ap.error("specify at least one author (or --all)")
    style = int(a.style) if a.style.isdigit() else a.style
    try:
        if a.emails:
            print(mailing_list(authors))
        else:
            latex = generate_latex_authors(authors, style, corresponding=a.corresponding)  # fails immediately if any keyword is wrong
            if not a.no_emails:  # as in the IDL macro: mailing list first, then LaTeX
                print(mailing_list(authors), end="\n\n")
            print(latex)
            hint = STYLE_HINTS.get(STYLE_NUMBERS.get(style, style))
            if hint:
                print("Note:", hint, file=sys.stderr)
    except (KeyError, ValueError) as err:
        sys.exit(str(err.args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
