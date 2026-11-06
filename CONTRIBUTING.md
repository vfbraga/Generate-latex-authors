# Contributing

Contributions are welcome **only to `authors_db.py`**: add yourself, a
collaborator, or a new institute. Pull requests that change other files are
rejected automatically (changes to the program itself are made by the
maintainer).

## How to submit a change

1. Fork the repository (or create a branch, if you have write access).
2. Edit `authors_db.py` (see below).
3. Run the consistency check and fix everything it reports:
   ```bash
   python generate_latex_authors.py --check
   ```
   Lines starting with `(info)` are not errors (e.g. an institute not used yet,
   which is expected when you add a new one before the authors that use it).
4. Open a pull request. The same check is run automatically on GitHub.

## Adding an institute

Add an entry to `INSTITUTES`:

```python
"oa_roma": {
    "full": "INAF-Osservatorio Astronomico di Roma, via Frascati 33, 00078 Monte Porzio Catone, Italy",
    "short": "INAF-Osservatorio Astronomico di Roma, Monte Porzio Catone, Italy",
},
```

- The key is short, lowercase, ASCII, with underscores, and must be unique.
- `full` is the complete affiliation as it must appear in the paper (LaTeX).
- `short` is the abbreviated version (city and country, no street) used for arXiv.
- Accents in LaTeX form (`Universit\`a`, `K\"oln`, `Andr{\'e}s`). Use a raw string
  (`r"..."`) when the text contains a backslash.
- Check that the institute is not already there under another key.

## Adding an author

Add an entry to `AUTHORS`:

```python
"braga": {
    "name": "V.~F.~Braga",
    "name_arxiv": "V.F. Braga",
    "email": "vittorio.braga@inaf.it",
    "orcid": "0000-0001-7511-2830",
    "affiliations": ["oa_roma"],
},
```

- The key is short, lowercase, ASCII, with underscores (usually the surname; add the
  initial if needed, e.g. `minniti_d`).
- `name`: LaTeX, initials separated by `~` (non-breaking space), accents in LaTeX form.
- `name_arxiv`: plain text, as it must appear in the arXiv author field.
- `orcid`: the 16-character ORCID string, or `None`.
- `affiliations`: a list of keys of `INSTITUTES`; they must exist. For the `aastex63`
  and `aastex701` styles the affiliations are printed in the order of this list.
- `aliases` (optional): a list of other names by which the author can be called.

## Privacy

The database contains email addresses and ORCIDs. Add only people who agreed to
be listed, and do not make this repository public without asking them.

## Reviewing

`authors_db.py` is Python code and is executed by the program and by the automatic
check: reviewers should read the diff and not only the check result.
