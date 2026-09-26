# Moving this work to a repo you can make private

## The blocking fact

**GitHub will not let a fork become private.** `amitrintzler/LTX-Video` is a
fork of `Lightricks/LTX-Video`, and for any fork the *Change visibility*
control is disabled. There is no setting to toggle. The only route is to create
a brand-new private repository and push this history into it.

A second fact worth saying plainly: **this repository has been public the whole
time.** Making the new one private protects what you push *from now on*. It does
not retract 260 public commits — anything already pushed has been readable, and
may be cached by GitHub, forks, or crawlers. Treat every credential that has
ever been in this history as exposed, even though the scan below is clean.

## One assumption of yours that is wrong, and it's good news

> "we didnt took updated for very long"

You are **not behind**. Measured on 2026-09-26:

```
upstream commits we don't have:  0
our commits upstream doesn't have: 260
```

`Lightricks/LTX-Video` last moved on **2026-01-05**. You have that commit.
Upstream has been still for nearly nine months, so nothing is waiting to be
merged and staying forked buys you nothing.

## What is actually yours

| Directory | Tracked files | Owner |
|---|---|---|
| `cinematic-pipeline/` | 151 | yours |
| `video-pipeline/` | 73 | yours |
| `remotion-videos/` | 49 | yours |
| `scripts/` | 7 | yours |
| `ltx_video/`, `configs/`, `tests/`, `inference.py`, `pyproject.toml` | — | Lightricks |

Your work is ~280 tracked files and touches none of the upstream model code.
You depend on `ltx_video` only through the LTX Desktop app, not through this
source tree.

## Three options

### A. Mirror everything into a new private repo (recommended)

Keeps all 260 commits and their reasoning, which is most of the value in this
history. Takes minutes.

```bash
gh repo create <you>/options-studio --private
git clone --mirror https://github.com/amitrintzler/LTX-Video.git /tmp/ltx-mirror
cd /tmp/ltx-mirror
git remote set-url --push origin https://github.com/<you>/options-studio.git
git push --mirror
```

Then repoint your worktrees (`git remote set-url origin …`) and keep the public
fork read-only, or delete it.

**Cost:** carries the upstream model code and the large blobs below.

### B. Fresh private repo, your code only

A clean repo containing just the four directories above. No upstream code, no
LTX history. Smallest and clearest, but **you lose the 260 commit messages**,
which in this project carry the record of what was tried and why.

### C. Mirror, then strip the heavy blobs

Option A followed by a history rewrite to drop generated media. The five
largest tracked blobs are all generated output:

```
21.2 MB  video-pipeline/output/trading-trailer-final.mp4
19.5 MB  video-pipeline/output/options-trailer-final.mp4
 7.2 MB  cinematic-pipeline/trailers/options-chain/cinematic/chain_cine_a.mp4
 7.0 MB  cinematic-pipeline/trailers/open-world/cinematic/cine_a.mp4
 5.6 MB  cinematic-pipeline/trailers/open-world/cinematic/cine_b.mp4
```

Rewriting history changes every commit hash and breaks existing clones. Worth
it only if repo size becomes a real problem; at 96 MB it is not yet.

## Recommendation

**Option A**, then add a `.gitignore` rule for `video-pipeline/output/` and
`cinematic-pipeline/trailers/**/cinematic/` so new renders stop entering history.
Renders belong on R2 or the local render root, which is already how the site
video ships.

## Before you push anywhere private

1. **Scan the history for secrets.** Run it against the mirror, not the worktree:
   `gitleaks detect --source /tmp/ltx-mirror --no-git` (this repo's sibling
   already uses gitleaks in CI). A scan of the current branch for key-shaped
   strings came back clean, but that checked one branch, not 260 commits.
2. **Move the credentials that live outside git** — `~/.codex/config.toml`,
   `~/LTX-Studio/youtube_client_secret.json`, `~/LTX-Studio/youtube_token.json`.
   They are correctly outside the repo today; keep it that way.
3. **Decide the fork's fate.** Deleting it removes the public copy going
   forward; it does not unpublish what was already there.

## What stays where it is

`optionseducator` is a separate private-facing repo and is unaffected. The site
video now ships from Cloudflare R2, not from git, so none of this touches
delivery.
