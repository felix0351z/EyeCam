// Kleine REST-API fuer das Kontaktformular
// Endpunkte:
//   GET    /api/health          -> Statuscheck
//   GET    /api/messages        -> alle gespeicherten Nachrichten
//   POST   /api/contact         -> neue Nachricht anlegen
//   DELETE /api/messages/:id    -> einzelne Nachricht loeschen
//
// Speicherung erfolgt der Einfachheit halber in einer lokalen JSON-Datei
// (messages.json). Fuer ein echtes Deployment wuerde man stattdessen eine
// Datenbank verwenden.

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'messages.json');

app.use(cors()); // [Platzhalter: fuer Produktion auf eure Domain einschraenken]
app.use(express.json());

// ---------- Hilfsfunktionen ----------

function readMessages() {
  if (!fs.existsSync(DATA_FILE)) {
    return [];
  }
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    console.error('Konnte messages.json nicht lesen:', err);
    return [];
  }
}

function writeMessages(messages) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(messages, null, 2), 'utf-8');
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ---------- Routen ----------

// Statuscheck, um zu pruefen ob die API laeuft
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Alle Kontaktnachrichten abrufen
app.get('/api/messages', (req, res) => {
  const messages = readMessages();
  res.json(messages);
});

// Neue Kontaktnachricht anlegen (wird vom Formular auf kontakt.html aufgerufen)
app.post('/api/contact', (req, res) => {
  const { name, email, message } = req.body || {};

  if (!name || !email || !message) {
    return res
      .status(400)
      .json({ error: 'Bitte Name, E-Mail und Nachricht ausfuellen.' });
  }

  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Bitte eine gueltige E-Mail-Adresse angeben.' });
  }

  const messages = readMessages();

  const entry = {
    id: crypto.randomUUID(),
    name: String(name).trim(),
    email: String(email).trim(),
    message: String(message).trim(),
    receivedAt: new Date().toISOString(),
  };

  messages.push(entry);
  writeMessages(messages);

  res.status(201).json({ message: 'Danke! Eure Nachricht wurde verschickt.', id: entry.id });
});

// Einzelne Nachricht loeschen (z. B. fuer eine kleine Admin-Ansicht)
app.delete('/api/messages/:id', (req, res) => {
  const messages = readMessages();
  const filtered = messages.filter((m) => m.id !== req.params.id);

  if (filtered.length === messages.length) {
    return res.status(404).json({ error: 'Nachricht nicht gefunden.' });
  }

  writeMessages(filtered);
  res.json({ message: 'Nachricht geloescht.' });
});

app.listen(PORT, () => {
  console.log(`Kontakt-API laeuft auf http://localhost:${PORT}`);
});
