# [Platzhalter: Projektname] — Website

Statische Website + kleine REST-API fuer das Schulprojekt (Hinderniserkennung
per Kamera, BLE-Uebertragung an zwei haptische Armbaender).

## Struktur

```
website/
├── index.html            Startseite / Projektuebersicht
├── funktionsweise.html    Technischer Aufbau
├── team.html              Team-Seite
├── kontakt.html           Kontaktformular
├── css/style.css          Gemeinsames Stylesheet
├── js/main.js             Navigation + Formular-Logik (REST-API-Aufruf)
└── api/                   Kleines Node.js/Express-Backend
    ├── server.js
    └── package.json
```

Alle Textstellen mit `[Platzhalter: ...]` sind fuer euren eigenen Inhalt
gedacht — einfach in den .html-Dateien durchsuchen und ersetzen.

## Website lokal ansehen

Einfach `index.html` (bzw. eine der anderen .html-Dateien) im Browser oeffnen.
Kein Server noetig, solange ihr nicht das Kontaktformular testen wollt.

## REST-API starten

Voraussetzung: [Node.js](https://nodejs.org) ist installiert.

```bash
cd api
npm install
npm start
```

Die API laeuft danach unter `http://localhost:3000`.

### Endpunkte

| Methode | Pfad                | Zweck                              |
|---------|---------------------|-------------------------------------|
| GET     | `/api/health`        | Statuscheck                        |
| GET     | `/api/messages`       | Alle Kontaktnachrichten abrufen    |
| POST    | `/api/contact`        | Neue Nachricht anlegen             |
| DELETE  | `/api/messages/:id`   | Nachricht loeschen                 |

Nachrichten werden der Einfachheit halber in `api/messages.json`
gespeichert (wird automatisch beim ersten Eintrag erstellt).

## Formular mit der API verbinden

In `js/main.js` die Konstante `API_BASE_URL` auf die Adresse eurer laufenden
API setzen, z. B.:

```js
const API_BASE_URL = 'http://localhost:3000';
```

Sobald ihr die API irgendwo deployt (z. B. auf einem Schulserver oder einem
kostenlosen Hosting-Dienst), hier einfach die entsprechende URL eintragen.
