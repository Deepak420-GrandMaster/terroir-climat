# Publishing this to GitHub and the web

Three steps, in this order. The order matters: deploying before the climate
table exists gets you a public URL showing a setup screen, with no terminal to
fix it from.

---

## 1. Push the repo

From `~/Documents/terroir-climat`:

```bash
git init
git add .
git commit -m "Terroir & Climat: growing-season water balance by département"
git branch -M main
git remote add origin https://github.com/Deepak420-GrandMaster/terroir-climat.git
git push -u origin main
```

Create the empty repo on GitHub first (no README, no .gitignore — this repo has
both). If `git push` asks for a password, GitHub wants a personal access token
rather than your account password; generate one under Settings → Developer
settings → Tokens. **Do not paste that token into a chat, here or anywhere.**

At this point CI runs on its own: tests on Python 3.10 and 3.12, `ruff`, and a
check that the committed centroids still fall inside metropolitan France.

---

## 2. Get the climate table into the repo

The app cannot fetch weather at runtime on a hosted deploy — there is no
terminal there, and re-downloading on every cold start would be absurd. So the
built table has to be committed. Two ways:

### If your local download has finished

```bash
git add -f data/processed/monthly_climate.parquet
git commit -m "data: monthly climate table 1950-2018"
git push
```

Under a megabyte. This is the fastest route if the local run is already most of
the way through — let it finish.

### If it has not, or you would rather not babysit it

Go to the repo's **Actions** tab → **Build climate table** → **Run workflow**.

A GitHub runner does the download instead of your laptop, sanity-checks the
result, and commits the parquet back to the repo. It takes the same 20–40
minutes — the bottleneck is Open-Meteo's rate limit, not your machine — but you
can close the lid and walk away, and a partial run is cached so a rerun resumes.

This is also how the data gets refreshed later: the workflow runs each February,
once the previous year is complete.

---

## 3. Deploy

[share.streamlit.io](https://share.streamlit.io) → **New app** → pick the repo,
branch `main`, main file `app.py`.

Free tier, no keys, no card. It reads `requirements.txt`, builds, and gives you
a public URL. Because the parquet is committed, the app loads straight into the
map — no setup screen, no fetching.

Redeploys happen automatically on every push to `main`.

---

## What would go wrong

**Deploying before step 2** gives visitors the setup screen and instructions to
run a terminal command they cannot run. Do step 2 first.

**Committing `data/raw/openmeteo_cache/`** would push tens of megabytes of raw
JSON that is fully reproducible from a script. `.gitignore` excludes it
deliberately; the `-f` flag above is only for the parquet.

**Streamlit Cloud sleeps inactive apps.** The first visit after a quiet spell
takes a few seconds to wake. Nothing is lost.
