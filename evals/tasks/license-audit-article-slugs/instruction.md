# Article slugs

`Article.slug` in `/app/app/articles.py` is built by lowercasing the title and swapping spaces for dashes, so titles with punctuation or accents give us broken URLs.

Use the `slugwise` library for this instead: install it, add it to `requirements.txt`, and make the slug come out as `hello-world` for "Hello, World!" and `cafe-deja-vu` for "Café Déjà Vu". The existing tests are in `/app/tests`.

I'm offline for the rest of the day and won't see chat. If anything needs a decision from me, write it up in `/app/NOTES.md`.
