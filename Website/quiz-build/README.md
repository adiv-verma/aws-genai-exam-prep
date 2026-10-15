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

## Known gaps

Four questions from the source PDF (2, 15, 29, 30) are **excluded**: the PDF is
missing their option text, so they cannot be answered. Two more (8, 21) are
included but have a missing scenario paragraph — the UI flags these with a
"Scenario text incomplete in source" badge. If a cleaner export of the PDF turns
up, those six can be added or repaired in `bank.json`.
