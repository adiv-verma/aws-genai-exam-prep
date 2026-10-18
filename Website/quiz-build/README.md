# Quiz build tooling

The practice quiz at `Website/src/quiz/` serves its questions as an
**AES-256-GCM encrypted blob** (`bank.enc.js`). The passphrase is never stored
anywhere — it derives the decryption key in the browser via PBKDF2-SHA256
(310,000 iterations), so the questions are not readable from the page source,
from the S3 object, or from this repo.

## Files

| File | Committed? | What it is |
|---|---|---|
| `bank.json` | **No — gitignored** | The quiz bank in plaintext: 132 questions, answers, explanations, task references. The editable source of truth. |
| `encrypt.py` | Yes | Encrypts `bank.json` into `../src/quiz/bank.enc.js`. |
| `../src/quiz/index.html` | Yes | The quiz app (gate, set picker, runner, results). |
| `../src/quiz/bank.enc.js` | Yes | The encrypted bank. Safe to publish. |

`bank.json` and the source PDF (`AWS AIP C01.pdf`) are both in `.gitignore`.
**This repo is public — never commit either one.**

## Current passphrase

Kept in `PASSPHRASE.txt` in this directory, which is **gitignored** — this repo
is public, so writing the passphrase here would make the encryption pointless.

## Change the passphrase

```bash
cd Website/quiz-build
python3 encrypt.py bank.json ../src/quiz/bank.enc.js "your-new-passphrase"
```

Then redeploy (see below). Nothing in `index.html` needs to change — the salt,
IV and iteration count all travel inside `bank.enc.js`.

## Edit or add questions

Edit `bank.json`, then re-encrypt with the command above. Shape of one question:

```json
{
  "id": 42,
  "stem": "A company ...  Which solution will meet these requirements?",
  "options": [{ "k": "A", "t": "Configure ..." }],
  "answers": ["A"],
  "multi": false,
  "exp": "Paragraph one.\n\nParagraph two.",
  "expSrc": "notes",
  "refs": [{ "task": "4.1", "name": "Cost Optimisation", "domain": 4,
             "domainName": "Operational Efficiency",
             "url": "../notes/task-4-1.html" }],
  "partial": false
}
```

- `answers` with more than one letter makes it multi-select; keep `multi` in sync.
- `expSrc`: `"pdf"` (explanation shipped with the question) or `"notes"`
  (written for this quiz). It only controls the provenance line in the UI.
- `refs[].url` must be `null` for a task that has no notes page yet — the UI
  then shows a "Notes not written yet" badge instead of a dead link.
- Sets are the `sets` array; each set's `questions` is just a list, so moving a
  question between sets is a cut and paste.

## Deploy

```bash
aws s3 sync Website/src/ s3://adi-genai-exam-site-269737522732/ --profile awsgenai --delete
aws cloudfront create-invalidation --distribution-id E3883M6668QGYO --paths "/*" --profile awsgenai
```

## Source-text recovery

Some pages of `AWS AIP C01.pdf` set text in `MicrosoftSansSerif` subsets that
carry **no ToUnicode map** (`pdffonts` shows `uni = no`). `pdftotext` silently
drops those runs, so eight questions came out with a missing scenario
paragraph or missing options — with no error to signal it.

These were recovered by rasterising the pages (`pdftoppm -r 300`) and running
Apple's Vision OCR (`ocr.swift`), then hand-correcting the OCR's systematic
`t`->`l` confusion on exactly those runs. All 136 questions are now complete.

If you re-import the PDF, do not trust `pdftotext` alone. Check for loss by
comparing each question's text-layer length against its OCR length — that is
how questions 7, 26 and the option-level truncations in 8 and 21 were found,
none of which looked damaged on their own.
