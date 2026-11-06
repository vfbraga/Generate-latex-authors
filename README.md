# Generate LaTeX authors

Generate the author list, the numbered affiliations and the mailing list of a
paper from a shared database of authors and institutes, in the format required
by the journal.

Supported styles:

| Style       | Journal / use                                   |
|-------------|--------------------------------------------------|
| `apj_old`   | ApJ, old `\altaffilmark` / `\altaffiltext` style |
| `aa`        | A&A (`\inst`, `\institute`)                      |
| `mnras`     | MNRAS                                            |
| `arxiv`     | plain text for the arXiv author field            |
| `aastex63`  | AASTeX 6.3 (`\author[orcid]`, `\affiliation`)    |
| `aastex701` | AASTeX 7.0.1 (with optional corresponding author) |

It is a Python translation of the IDL macro `generate_latex_authors.pro`.

## Installation

Requirements: Python 3.8 or later. No external packages are needed.

```bash
git clone https://github.com/<owner>/generate-latex-authors.git
cd generate-latex-authors
```

(or use *Code → Download ZIP* on GitHub and unzip it). Keep
`generate_latex_authors.py` and `authors_db.py` in the same folder.

## Usage

Authors are given in the order in which they appear in the paper, by database
key (`braga`), alias, or name (`"V.~F.~Braga"`, `"V.F. Braga"`); upper/lower case
does not matter.

```bash
# emails (one per line) followed by the LaTeX
python generate_latex_authors.py braga stetson bono --style mnras

# LaTeX only
python generate_latex_authors.py braga stetson bono --style aa --no-emails

# mailing list only
python generate_latex_authors.py braga stetson bono --emails

# AASTeX 7.0.1, with Braga as corresponding author (the only one whose email is shown)
python generate_latex_authors.py braga stetson bono -s aastex701 -c braga --no-emails

python generate_latex_authors.py --list     # all the author keys
python generate_latex_authors.py --check    # consistency checks on the database
```

If one or more keywords are not recognized, the program lists all of them
(with suggestions) and prints nothing else.

From Python:

```python
from generate_latex_authors import generate_latex_authors, mailing_list

authors = ["braga", "stetson", "bono"]
print(generate_latex_authors(authors, style="aastex701", corresponding="braga"))
print(mailing_list(authors))
```

Institutes are numbered 1, 2, ... in order of first appearance in the author
list; the numbers of each author are printed in increasing order.

## Adding authors and institutes

Everything is in `authors_db.py`. See [CONTRIBUTING.md](CONTRIBUTING.md).
