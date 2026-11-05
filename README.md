# GewinnspielRadar

Browser-App für iPhone, iPad und PC zur täglichen Suche nach öffentlich ausgeschriebenen Gewinnspielen. Die Oberfläche wird als statische Seite über **GitHub Pages** angeboten, die Suche läuft täglich über **GitHub Actions**. Keine Anmeldung, keine persönlichen Daten und keine automatische Gewinnspielteilnahme.

## Einmalig GitHub Pages aktivieren

1. Im Repository auf **Settings → Pages** gehen.
2. Unter **Build and deployment → Source** **GitHub Actions** auswählen.
3. **Actions → Gewinnspiele suchen und veröffentlichen → Run workflow** starten.
4. Nach erfolgreichem Lauf sollte die App unter **https://bernd72.github.io/GewinnspielRadar/** erreichbar sein.

Der automatische Lauf ist täglich auf **07:17 UTC** angesetzt (in Deutschland 08:17 Uhr im Winter / 09:17 Uhr im Sommer). GitHub kann geplante Läufe verzögern oder bei längerer Inaktivität deaktivieren.

## Funktionen

- Öffentlich zugängliche Übersichtsseiten von Mitspiel, GewinnHai und GiveOwl werden abgefragt, **sofern robots.txt die Abfrage zulässt**.
- Titel, Teilnahmeschluss, Link und Quelle werden aus erkennbaren HTML-Einträgen übernommen. Seitenlayoutänderungen können zu leeren oder fehlerhaften Ergebnissen führen.
- Abgelaufene Einträge werden entfernt; Links werden dedupliziert.
- Suche, Quellenfilter, Fristsortierung, regionale Stichwortsuche.
- Favoriten und erledigte Einträge lassen sich markieren; sie bleiben nur **im lokalen Browser** (localStorage). Über Export/Import können sie auf andere Geräte übertragen werden.
- Fehler oder nicht erreichbare Quellen werden im Status der Web-App angezeigt.

## Wichtige Grenzen

**Alle Treffer sind ungeprüfte Hinweise**, keine Seriositäts- oder Datenschutzfreigabe. Kaufpflicht, Newsletterzwang, Werbung Dritter oder Automatisierungsverbote werden noch nicht zuverlässig erkannt. Die tatsächlichen Gewinnchancen sind unbekannt. Bitte die Teilnahmebedingungen und das Impressum vor einer Anmeldung prüfen.

**Keine automatische Teilnahme:** Die App übermittelt keinen Namen, keine E-Mail-Adresse und keine Kontaktdaten. Es werden keine Formulare ausgefüllt und keine CAPTCHA-Prüfungen umgangen.

## Technische Dateien

- `index.html`: Responsive Weboberfläche
- `icon.svg`: App-Symbol
- `data/gewinnspiele.json`: täglich generierter Datensatz
- `scripts/collect.py`: vorsichtiger Python-Sammler
- `.github/workflows/aktualisieren.yml`: Such- und Veröffentlichungsworkflow
- `requirements.txt`: Python-Abhängigkeiten

## Lokal ausprobieren

```powershell
py -m pip install -r requirements.txt
py scripts/collect.py
py -m http.server 8080
```

Danach `http://localhost:8080` öffnen. Beim erstmaligen Laden ohne erfolgreiche Suche können keine echten Einträge angezeigt werden.

## Datenschutz und Kosten

Die Weboberfläche hat keine Werbetracker oder externen JavaScript-Bibliotheken. GitHub kann technische Zugriffsprotokolle führen. Der Sammler ruft nur öffentliche Listen ab und prüft robots.txt; darüber hinaus sind die Nutzungsbedingungen der Quellen zu respektieren. Für kleine öffentliche Projekte sind GitHub Actions und GitHub Pages im Rahmen der jeweils geltenden GitHub-Limits normalerweise kostenfrei.
