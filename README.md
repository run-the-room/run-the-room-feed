# Run the Room — Public Feed

Public RSS feed and episode index pages for the **Run the Room** podcast:
one meeting type each week, in three parts — Planning, Running, Follow-up —
across every industry.

- **RSS feed:** `feed.xml` (served at
  `https://run-the-room.github.io/run-the-room-feed/feed.xml`)
- **Meeting-type index pages:** one per type (see `meeting-types.json`),
  e.g. `iep-meeting.html`, `school-board-meeting.html`
- **Cover:** `cover.png` (1600x1600)

## How it works

The `.github/workflows/update-feed.yml` Action runs daily (~8:20 AM ET) and on
manual dispatch. It:

1. Pulls the upstream author feed from
   `https://muse.ai/podcasts/feed/1337692426099284/46958af6-3f81-48da-90a8-95c133c7c40f`
2. Strips any GUIDs listed in `EXCLUDED_GUIDS` (used when a corrected
   "Revised" edition replaces an original episode)
3. Normalizes the iTunes author/category/owner tags, sets the channel image to
   `cover.png`, and fixes the self link
4. Writes `feed.xml`, then runs `build-index.py` to regenerate all index pages
5. Commits and pushes anything that changed (GitHub Pages serves the site)

## Setup notes

- GitHub Pages must be enabled on this repo (source: main branch, root).
- To pull an episode from the public feed, add its GUID to `EXCLUDED_GUIDS`
  in the workflow file and re-run the workflow.
- `build-index.py` groups episodes by meeting type from `meeting-types.json`.
  Episode titles must start with the meeting type name
  (e.g. "IEP Meeting, Part 1: Planning — ...").
