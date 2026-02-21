# GitHub + Public Demo Deployment Plan

## 1. Pushing to GitHub

### 1.1 Repo setup (one-time)

- **Create repo on GitHub:** New repository (e.g. `atheria` or `biochem-section-finder`), no need to add README/license if you already have them locally.
- **Add a project `.gitignore`** so you don’t commit venvs, index artifacts, or secrets. Suggested contents (see below): Python venv, `__pycache__`, `data/index/`, `data/raw/*` (optional), `.env`, IDE/OS cruft.
- **Optional:** Add a permissive license (e.g. MIT) and keep README accurate (setup, run, seed paper).

### 1.2 Initial push

```bash
cd /path/to/Atheria
git init
git add .
git commit -m "Initial commit: Atheria section finder MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 1.3 What to commit vs ignore

- **Commit:** `src/`, `frontend/`, `docs/`, `eval/`, `requirements.txt`, `pyproject.toml` (if any), `README.md`, `.gitignore`, optional small sample data under `data/` if you want “run out of the box.”
- **Ignore:** `.venv/`, `data/index/` (built index can be large; rebuild or attach as release artifact), `data/raw/*.htm` / `*.xml` if large, `.env`, `*.pyc`, `__pycache__/`, ChromaDB/IDE/OS files.

### 1.4 Optional: CI

- **GitHub Actions:** e.g. run tests/lint on push (e.g. `pytest`, `ruff`). Can add a job that builds the index from a tiny sample and runs a smoke test so the repo stays runnable.

---

## 2. Is Vercel a good fit?

**Short answer: not for the current app.**

- **What Vercel does well:** Static sites, Next.js, serverless functions (short, stateless requests). Free tier is generous for that.
- **What Atheria needs:** A **long‑running Python process** that:
  - Loads **MedCPT** (Article/Query encoder + Cross-Encoder) and **ChromaDB** at startup.
  - Serves **Streamlit** (or FastAPI + your retrieval logic) with the **prebuilt index** on disk (or equivalent).
- **Why that clashes with Vercel:** Vercel runs short-lived serverless invocations. It doesn’t run a persistent Streamlit server or keep a large in-memory/on-disk index. You’d hit cold starts, time/memory limits, and no native “run Streamlit here” story.

**When Vercel *could* be used later:** If you split the system into (1) a **static or Next.js frontend** that calls (2) a **separate backend API** (hosted elsewhere, e.g. Railway/Render/HF), then the frontend alone could be deployed on Vercel. The heavy part (models + index) would still live on that other backend.

---

## 3. Lightweight deployment options for a public demo

These keep a **single deployable app** (Streamlit + models + index) and are more suitable than Vercel for a demo.

### Option A: Streamlit Community Cloud (simplest)

- **What:** Free hosting for Streamlit apps; connects to your GitHub repo.
- **Pros:** No Docker; push to GitHub, connect repo, set run command and branch; automatic redeploys.
- **Cons:** Memory limits (~1 GB on free tier); first run downloads MedCPT and builds/loads index — use a **small prebuilt index** or build once in a startup script so the app stays within limits and starts in reasonable time.
- **Steps (high level):**
  1. Push repo to GitHub (including a small `data/index/` or a script that builds it from a tiny sample on first run).
  2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, deploy from repo.
  3. **Main file:** `frontend/app.py`.
  4. **Run command:** `streamlit run frontend/app.py --server.headless true`.
  5. Set **Python version** (e.g. 3.10/3.11) and ensure `requirements.txt` (and optional `packages.txt` for system deps) are at repo root.
  6. If the index is large, either (a) commit a minimal index (one small paper) or (b) build index in a one-off script and cache it (e.g. in a GitHub Action that produces an artifact and the app downloads it at startup — more involved).

### Option B: Hugging Face Spaces (good for ML demos)

- **What:** Host Streamlit (or Gradio) apps; optional GPU.
- **Pros:** Free tier, ML-friendly, good for “demo with models”; can store a small index in the Space or in HF datasets.
- **Cons:** Similar need to keep index + model load within resource limits.
- **Steps (high level):**
  1. Create a new Space, choose **Streamlit**.
  2. Push your app (e.g. `frontend/app.py` as `app.py`) and `requirements.txt`; add a small `data/index/` or a script that builds it.
  3. Configure Space to use the same run command as above; rely on HF’s caching for Transformers/MedCPT if possible.

### Option C: Docker + Railway / Render / Fly.io (most control)

- **What:** Package the app (Streamlit + index + deps) in a **Dockerfile**; run the container on Railway, Render, or Fly.io.
- **Pros:** Full control over environment, can attach a volume for a larger index or build it in the image; avoids Streamlit Cloud memory limits.
- **Cons:** You maintain Docker and deploy config; free tiers have limits.
- **Steps (high level):**
  1. Add a **Dockerfile** that: uses a Python image, installs deps from `requirements.txt`, copies `src/`, `frontend/`, and (optionally) `data/index/`, sets `WORKDIR` and `CMD` to run `streamlit run frontend/app.py`.
  2. Optionally use a **.dockerignore** (e.g. ignore `.venv`, `data/raw`, large files).
  3. Connect the repo to Railway/Render/Fly.io and deploy from the Dockerfile (or from a `docker-compose.yml` if you add more services later).

---

## 4. Recommended path for “lightweight + public demo”

1. **GitHub:** Add `.gitignore`, push the repo, optionally add a minimal CI (tests + smoke test with small index).
2. **Demo:** Start with **Streamlit Community Cloud** (Option A): one paper’s index in the repo (or built from a tiny sample in the app/script), `streamlit run frontend/app.py` as the run command. If you hit memory or startup limits, switch to **Hugging Face Spaces** (Option B) or **Docker + Railway/Render** (Option C).
3. **Vercel:** Skip for the current monolithic Streamlit app; consider it later only if you introduce a separate frontend that talks to an API hosted elsewhere.

---

## 5. Minimal checklist before first deploy

- [ ] `.gitignore` in place (venv, `data/index/`, large raw files, `.env`).
- [ ] `README.md` has clear setup and run instructions.
- [ ] Either commit a **small** `data/index/` (one paper) or document how to build it so the deployed app can load an index (e.g. run a script once or download from a release).
- [ ] `requirements.txt` is at repo root and pins versions if needed for reproducibility.
- [ ] Streamlit entrypoint is `frontend/app.py` and runs from **project root** (so `INDEX_DIR` and paths in config resolve correctly); in Cloud/Spaces, set “Working directory” to repo root if the platform allows it.
