#!/usr/bin/env python3
"""Öffentliche Gewinnspiel-Übersichten abrufen; keine automatische Teilnahme."""
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gewinnspiele.json"
UA = "GewinnspielRadar/1.0 (private nichtkommerzielle tägliche Übersicht)"
SOURCES = [
    ("Mitspiel", "https://mitspiel.com/neue-gewinnspiele"),
    ("GewinnHai", "https://www.gewinnhai.de/neu"),
    ("GiveOwl", "https://giveowl.com/c/de/"),
]
PLACE = re.compile(r"odenwald|oberzent|erbach|michelstadt|eberbach|heidelberg|mannheim|mosbach|weinheim|rhein.neckar|bergstraße|südhessen|hessen", re.I)
DATE = re.compile(r"\b(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(20\d{2})\b")
NAMED_DATE = re.compile(r"\b(\d{1,2})\s*\.?\s*(Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(20\d{2})\b", re.I)
MONTH = dict(zip("januar februar märz maerz april mai juni juli august september oktober november dezember".split(), [1,2,3,3,4,5,6,7,8,9,10,11,12]))
END = re.compile(r"Teilnahmeschluss|Enddatum|Teilnahme bis|Ende am|Einsendeschluss|Läuft bis", re.I)


def clean_url(raw):
    try:
        p = urlsplit(raw)
        if p.scheme not in ("https", "http") or not p.hostname:
            return ""
        return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/", "", ""))
    except ValueError:
        return ""


def deadline(text):
    match = DATE.search(text)
    if match:
        try:
            return date(int(match[3]), int(match[2]), int(match[1])).isoformat()
        except ValueError:
            return None
    match = NAMED_DATE.search(text)
    if match:
        try:
            return date(int(match[3]), MONTH[match[2].lower()], int(match[1])).isoformat()
        except (ValueError, KeyError):
            return None
    return None


def allowed(session, url):
    p = urlsplit(url)
    try:
        resp = session.get(f"{p.scheme}://{p.netloc}/robots.txt", timeout=12)
        if resp.status_code in (404, 410):
            return True, "Keine robots.txt vorhanden"
        if resp.status_code != 200:
            return False, f"robots.txt HTTP {resp.status_code}"
        rules = RobotFileParser()
        rules.parse(resp.text.splitlines())
        return rules.can_fetch(UA, url), "robots.txt ausgewertet"
    except requests.RequestException as exc:
        return False, f"robots.txt nicht abrufbar: {type(exc).__name__}"


def extract(source, base, html, today):
    soup = BeautifulSoup(html, "html.parser")
    seen, found = set(), []
    for h in soup.select("h3"):
        title = re.sub(r"^\d+\s*[.)]\s*", "", h.get_text(" ", strip=True)).strip()
        if len(title) < 8 or len(title) > 210 or title.lower() in ("gewinnspiel", "neue gewinnspiele", "startseite"):
            continue
        container = None
        node = h
        for _ in range(8):
            node = node.parent
            if not isinstance(node, Tag) or node.name in ("html", "body"):
                break
            text = node.get_text(" ", strip=True)
            if len(text) <= 1800 and len(node.find_all("h3")) == 1 and END.search(text):
                container = node
                break
        if container is None:
            continue
        text = container.get_text(" ", strip=True)
        marker = END.search(text)
        until = deadline(text[marker.end():marker.end()+110])
        if not until or until < today:
            continue
        anchors = container.find_all("a", href=True)
        anchor = None
        for label in ("Zum Gewinnspiel", "Details ansehen", "Teilnehmen", "Mehr erfahren"):
            anchor = next((a for a in anchors if label.lower() in a.get_text(" ", strip=True).lower()), None)
            if anchor:
                break
        if anchor is None:
            anchor = h.find("a", href=True) or next((a for a in anchors if len(a.get_text(" ", strip=True)) >= 8), None)
        if anchor is None:
            continue
        url = clean_url(urljoin(base, anchor["href"]))
        if not url or url in seen:
            continue
        seen.add(url)
        parts = list(container.stripped_strings)
        org = "Nicht angegeben"
        for i, part in enumerate(parts[:-1]):
            if part.lower().rstrip(":") in ("veranstalter", "anbieter"):
                org = parts[i+1][:100]
                break
        found.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:20],
            "title": title, "organizer": org, "deadline": until,
            "url": url, "source": source, "region": bool(PLACE.search(title + " " + org)),
        })
    return found


def main():
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    try:
        previous = json.loads(OUT.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        previous = {}
    old = {x["id"]: x for x in previous.get("items", []) if x.get("id") and x.get("source") != "Beispiel"}
    collected = dict(old)
    status = []
    with requests.Session() as session:
        session.headers["User-Agent"] = UA
        for name, url in SOURCES:
            permitted, why = allowed(session, url)
            if not permitted:
                entry = {"source": name, "ok": False, "detail": "Übersprungen: " + why}
                status.append(entry)
                print(entry, flush=True)
                continue
            try:
                r = session.get(url, timeout=25)
                r.raise_for_status()
                if "html" not in r.headers.get("Content-Type", "text/html") or len(r.content) > 3_000_000:
                    raise ValueError("Keine unterstützte HTML-Seite")
                items = extract(name, url, r.text, today)
                if not items:
                    raise ValueError("Keine gültigen Einträge gefunden; HTML-Struktur prüfen")
                for item in items:
                    old_item = old.get(item["id"], {})
                    item["found_at"] = old_item.get("found_at", today)
                    item["last_seen"] = today
                    collected[item["id"]] = item
                entry = {"source": name, "ok": True, "count": len(items)}
            except (requests.RequestException, ValueError) as exc:
                entry = {"source": name, "ok": False, "detail": str(exc)[:150]}
            status.append(entry)
            print(entry, flush=True)
    items = [it for it in collected.values() if it.get("deadline") and it["deadline"] >= today]
    items.sort(key=lambda it: (it["deadline"], it.get("title", "")))
    result = {"mode": "live", "updated_at": now.isoformat(timespec="seconds"), "sources": status, "items": items[:220]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Gespeichert: {len(result['items'])} Gewinnspiele")


if __name__ == "__main__":
    main()
