#!/usr/bin/env python3
"""Encrypt the quiz bank for the static site.

  python3 encrypt.py bank.json <out.js> "<password>"

Payload: gzip(JSON) -> AES-256-GCM, key = PBKDF2-HMAC-SHA256(password, salt, 310000).
The browser reverses this with WebCrypto + DecompressionStream, so the question
bank never exists in plaintext on the server or in the page source.
"""
import base64, gzip, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 310_000

src, out, password = sys.argv[1], sys.argv[2], sys.argv[3]

plain = gzip.compress(json.dumps(json.load(open(src)), separators=(',', ':')).encode(), 9)
salt = os.urandom(16)
iv = os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode())
ct = AESGCM(key).encrypt(iv, plain, None)

b64 = lambda b: base64.b64encode(b).decode()
payload = {"v": 1, "iter": ITER, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct), "gz": True}
with open(out, 'w') as f:
    f.write("window.__QUIZ_PAYLOAD__=" + json.dumps(payload) + ";\n")
print(f"wrote {out}  ({os.path.getsize(out):,} bytes)  plaintext {len(plain):,} bytes gzipped")
