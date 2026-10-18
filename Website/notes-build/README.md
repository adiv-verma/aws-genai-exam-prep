# notes-build

Generates the three cross-cutting pages in `Website/src/notes/`:

| Page | What it is |
|---|---|
| `concepts.html` | The concept index — 54 recurring ideas, each naming the task that owns the detail and what every other task adds. |
| `map.html` | The whole-exam map — all five domains as one request, plus the threads that cut across them. |
| `index.html` | The Study Notes hub — exam weights, per-task one-liners and concept chips. |

The 20 `task-*.html` pages and the 5 `domain-*.html` maps are **not** generated here; they
stay hand-authored, as before.

## Running it

```bash
python3 Website/notes-build/build.py
```

Writes straight into `Website/src/notes/`. No dependencies beyond the standard library.
Deploy afterwards the usual way (`aws s3 sync` + CloudFront invalidation).

## Files

- **`data.py`** — the content. Domain weights, the per-task one-liner and chips, and the
  54 concept entries. Each concept names an `owner` (task, anchor, section label, why it owns
  it) and a list of `also` entries (task, anchor, the different angle, the detail). Two
  concepts — Step Functions and CloudWatch — deliberately have `owner=None` and a `lead`
  instead, because the disambiguation *is* the entry.
- **`svgkit.py`** — SVG primitives matching the house style the domain maps already use
  (222×186 cards, the `5.9·len + 16` chip-width formula, numeric entities only), plus the
  six concept diagrams.
- **`build.py`** — page shells, CSS, the card renderer and the client-side filter.

## Editing

Almost every change is a `data.py` change. Anchors must match the real `id="s1"`/`id="t1"`
targets on the task pages — note **4.2 uses `t1`–`t6`** because its notes are headed "Topic",
not "Section". `build.py` does not validate anchors; check them after editing with:

```bash
python3 - <<'PY'
import re, os, glob
os.chdir("Website/src/notes")
ids = {f: set(re.findall(r'id="([^"]+)"', open(f).read())) for f in glob.glob("*.html")}
for f in ("concepts.html", "map.html", "index.html"):
    for h in set(re.findall(r'href="([^"#]+)#([^"]+)"', open(f).read())):
        if h[0] in ids and h[1] not in ids[h[0]]:
            print("BROKEN", f, "->", h)
PY
```
