#!/usr/bin/env python3
"""Build per-meeting-type index pages for the Run the Room podcast feed.

Reads feed.xml in this directory, groups episodes by meeting type
(matched from the start of each episode title), and writes:
  index.html            - show homepage with latest episodes + links to every type page
  <type-slug>.html     - one page per meeting type

Meeting types come from meeting-types.json in this directory.
Run after feed.xml is rebuilt. Safe to re-run; output is deterministic.
"""
import html
import json
import os
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FEED_FILE = os.path.join(HERE, "feed.xml")

# "Play episode" buttons link to the show's Apple Podcasts page so plays are
# countable (owner decision, Oct 25, 2026). Never link a button to an
# enclosure/.mp3 URL, and never use an inline <audio> player.
APPLE_URL = "https://podcasts.apple.com/podcast/id6825404495"
TYPES_FILE = os.path.join(HERE, "meeting-types.json")

PAGE_CSS = """
body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;max-width:860px;
margin:0 auto;padding:24px 16px;color:#1a1a1a;background:#fafafa}
header{border-bottom:3px solid #5c3a1a;margin-bottom:24px;padding-bottom:16px}
h1{color:#5c3a1a;margin:0 0 8px}
h2{color:#5c3a1a}
p.sub{color:#555;margin:0}
nav{margin:16px 0;padding:12px;background:#fff;border:1px solid #ddd;border-radius:8px}
nav a{margin-right:14px;color:#5c3a1a}
.ep{background:#fff;border:1px solid #ddd;border-radius:8px;padding:14px 16px;margin:0 0 14px}
.ep h3{margin:0 0 6px;font-size:1.05em}
.ep h3 a{color:#5c3a1a;text-decoration:none}
.ep .meta{color:#777;font-size:.85em;margin-bottom:6px}
.ep p{margin:6px 0 0;font-size:.92em;color:#333}
audio{width:100%;margin-top:8px}
.playbtn{display:inline-block;margin-top:10px;padding:9px 18px;background:#1a3a5c;color:#fff !important;border-radius:24px;text-decoration:none;font-weight:600;font-size:.95em}
.playbtn:hover{background:#2a5a8c}
footer{margin-top:32px;color:#888;font-size:.8em;border-top:1px solid #ddd;padding-top:12px}
"""


def parse_feed():
    tree = ET.parse(FEED_FILE)
    channel = tree.getroot().find("channel")
    show_title = channel.findtext("title") or "Run the Room"
    show_desc = (channel.findtext("description") or "").strip()
    items = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()
        guid_el = item.find("guid")
        guid = (guid_el.text or "").strip() if guid_el is not None else ""
        enc = item.find("enclosure")
        audio = enc.get("url", "") if enc is not None else ""
        dur = ""
        for child in item:
            if child.tag.endswith("}duration") or child.tag == "duration":
                dur = (child.text or "").strip()
        try:
            datestr = parsedate_to_datetime(pub).strftime("%B %d, %Y")
        except Exception:
            datestr = pub
        blurb = re.sub(r"<[^>]+>", "", desc)
        blurb = html.unescape(blurb).strip()
        if len(blurb) > 400:
            blurb = blurb[:397] + "..."
        items.append({
            "title": title, "datestr": datestr, "blurb": blurb,
            "guid": guid, "audio": audio, "dur": dur,
        })
    return show_title, show_desc, items


def episode_card(ep):
    t = html.escape(ep["title"])
    meta = html.escape(ep["datestr"])
    if ep["dur"]:
        meta += " &middot; " + html.escape(ep["dur"])
    blurb = html.escape(ep["blurb"])
    # Inline <audio> players can't follow the media host's redirect on iOS Safari,
    # so episode cards use a play button linking to the show's Apple Podcasts
    # page instead (direct enclosure plays can't be counted).
    player = (f'<a class="playbtn" href="{APPLE_URL}" target="_blank" rel="noopener">'
              f'&#9654; Play episode</a>') if ep["audio"] else ""
    return (f'<div class="ep"><h3>{t}</h3>'
            f'<div class="meta">{meta}</div><p>{blurb}</p>{player}</div>')


def page(title, heading, sub, nav_links, body_html):
    nav = " ".join(f'<a href="{html.escape(href)}">{html.escape(label)}</a>'
                   for label, href in nav_links)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header><h1>{html.escape(heading)}</h1><p class="sub">{html.escape(sub)}</p></header>
<nav>{nav}</nav>
{body_html}
<footer>Run the Room &middot; episodes also available in the
<a href="feed.xml">RSS feed</a></footer>
</body>
</html>
"""


def main():
    with open(TYPES_FILE, encoding="utf-8") as f:
        types = json.load(f)
    if not os.path.exists(FEED_FILE):
        print("feed.xml not found yet; nothing to index")
        return
    show_title, show_desc, items = parse_feed()

    groups = {m["slug"]: [] for m in types}
    other = []
    for ep in items:
        matched = None
        for m in types:
            if ep["title"].lower().startswith(m["type"].lower()):
                matched = m["slug"]
                break
        if matched:
            groups[matched].append(ep)
        else:
            other.append(ep)

    nav_links = [("All episodes", "index.html")]
    for m in types:
        nav_links.append((m["type"], m["slug"] + ".html"))

    for m in types:
        eps = groups[m["slug"]]
        body = (f"<h2>{len(eps)} episode{'s' if len(eps) != 1 else ''}</h2>\n"
                + "\n".join(episode_card(ep) for ep in eps)
                if eps else "<p>No episodes yet.</p>")
        href = m["slug"] + ".html"
        with open(os.path.join(HERE, href), "w", encoding="utf-8") as f:
            f.write(page(f"{m['type']} \u2014 Run the Room",
                         m["type"], "Planning, Running, Follow-up.",
                         nav_links, body))
        print(f"wrote {href} ({len(eps)} episodes)")

    latest = items[:20]
    body = "<h2>Latest episodes</h2>\n" + "\n".join(episode_card(ep) for ep in latest)
    if other:
        body += "<h2>More from the show</h2>\n" + "\n".join(episode_card(ep) for ep in other)
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(show_title, show_title,
                     show_desc or "One meeting type each week: planning, running, follow-up.",
                     nav_links, body))
    print(f"wrote index.html ({len(items)} total episodes)")


if __name__ == "__main__":
    main()
