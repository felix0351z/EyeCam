# Sensor-Integration (VL53L5CX) – Erklärung fürs Team

## Worum geht's?
EyeCam erkennt Hindernisse bisher nur mit der Kamera (YOLO). Die Kamera sagt
*was* da ist, aber nicht *wie weit weg* es ist. Der VL53L5CX misst genau das:
ein Raster aus 8x8 = 64 Entfernungsmessern, die gleichzeitig nach vorn schauen.
Ziel: verlässlicheres Warnen per Armband, und alles im Analyzer überwachbar.

## Die drei Messwerte pro Feld
| Wert | Bedeutung | Vergleich |
|---|---|---|
| `distance_mm` | Entfernung in mm | das Maßband |
| `target_status` | Ist die Messung gültig? (5 und 9 = ja) | der Türsteher |
| `range_sigma_mm` | Wie unsicher ist die Messung? | die Fehlertoleranz |

## Wie die Teile zusammenspielen
1. **Reader-Thread (`sensor/reader.py`)** liest den Sensor im Hintergrund und
   legt immer nur den neuesten Frame in einen "Briefkasten". YOLO (~12 fps) holt
   ihn ab, wenn es Zeit hat, und muss nie auf den Sensor (15 Hz) warten.
2. **`SensorZoneDetection`** teilt das Raster in links (Spalten 0-1), Mitte (2-5),
   rechts (6-7). Pro Zone: Anteil gültiger Felder, die näher als `NEAR_MM` sind.
3. **Entprellen:** Mittel über die letzten 5 Frames. Ein einzelner Ausreißer
   löst keinen Alarm aus (wie ein Taster, der nicht bei jedem Zucken schaltet).
4. **Entscheidung (`_decide`)**, jetzt in der Basisklasse für alle Algorithmen:
   Mitte blockiert -> zur freieren Seite ausweichen, beide Seiten blockiert -> STOP.
5. **Fallback:** Fällt der Sensor aus, läuft automatisch die YOLO-Erkennung
   weiter, und es gibt eine Warnung im Log.
6. **Analyzer:** Das `SensorPacket` wird mit Zeitstempel gesendet, damit man
   Sensor- und Kamerabild zeitlich zuordnen kann.

## Datei-Übersicht
| Datei | Änderung |
|---|---|
| `app/sensor/classes.py` | neu: `SensorFrame` (Datenbehälter) |
| `app/sensor/reader.py` | neu: Reader-Thread |
| `app/detection/classes.py` | `calculate(..., sensor=None)` und `_decide()` |
| `app/detection/zone_based.py` | Signatur angepasst, nutzt `_decide()` (Verhalten gleich) |
| `app/detection/sensor_zone.py` | neu: Sensor-Erkennung mit Fallback |
| `app/main.py` | Sensor starten, Frames senden, Algorithmus wählen |
| `proto/packets.proto` | `SensorPacket.timestamp_ms = 4` |
| `app/sender.py` | `send_sensor_packet` ergänzen (siehe `sender_snippet.py`) |

## Einbauen (Reihenfolge)
```bash
git checkout main && git pull
git checkout -b feature/sensor-integration
```
1. Dateien aus diesem Ordner in das Repo kopieren (`main.py`, `detection/classes.py`
   und `detection/zone_based.py` ersetzen die bisherigen; bitte per `git diff` prüfen).
2. `config.txt` auf dem Pi: `dtparam=i2c_arm_baudrate=1000000`, dann neu starten.
3. `pip install sparkfun-qwiic-vl53l5cx` (Name ggf. gegen die Doku prüfen).
4. Proto-Datei ersetzen und Code **für App und Analyzer** neu generieren:
   `protoc -I proto --python_out=app/api --pyi_out=app/api proto/packets.proto`
   (Pfade ggf. anpassen).
5. `send_sensor_packet` in `sender.py` einfügen. Bis dahin
   `SEND_SENSOR_TO_ANALYZER = False` in `main.py` lassen.
6. Analyzer: Bytes dekodieren (`analyzer_decode_snippet.py`), danach `SEND_SENSOR_TO_ANALYZER = True`.

## Testen
- **Raster-Orientierung:** Hand links vor den Sensor halten. Erscheint sie rechts?
  Dann `FLIP_LR = True` in `reader.py` setzen. Das Gleiche für oben/unten (`FLIP_UD`).
- **Boden:** Sieht der Sensor den Boden und gibt Fehlalarme? Dann in `sensor_zone.py`
  `ROWS = slice(0, 6)` setzen.
- **Ausfall:** Sensor abstecken. Das Programm muss weiterlaufen und im Log warnen.
- **FPS:** YOLO soll nicht unter ca. 12 fps fallen.

## Tuning (im Analyzer beobachten)
| Wert (`sensor_zone.py`) | Start | Wirkung |
|---|---|---|
| `NEAR_MM` | 1500 | ab welcher Entfernung gilt etwas als Hindernis |
| `MAX_SIGMA` | 20 | höher = mehr Messungen zählen, aber unsicherer |
| `MOVE_THRESHOLD` | 0.5 | Anteil naher Felder, ab dem ausgewichen wird |
| `VALID_STATUS` | (5, 9) | testweise 6 ergänzen |
| `WINDOW` | 5 | größer = ruhiger, aber träger |

## Bekannte Stolperfallen
- Es darf **nur ein** Algorithmus aktiv sein (sonst doppelte Armband-Impulse).
- Schwarze oder spiegelnde Flächen liefern oft Aussetzer statt Distanz. Ungültige
  Felder zählen aktuell als "frei". Im Analyzer die Statusverteilung beobachten.
- Der Sensor-Start (Firmware-Upload) dauert einige Sekunden.
- Die Methodennamen der Sparkfun-Lib wurden nicht auf dem Gerät getestet.
  Bei Fehlern in `reader.py` gegen die Doku prüfen.
- Der Cooldown (2 s) in `_move` begrenzt nur die Ausgaberate. Das Entprellen
  passiert vorher im Mittel über die Frames.

## Testen ohne Sensor
1. **Unit-Tests (auch am PC):** `pip install pytest numpy`, dann `cd app && python -m pytest ../tests -v`
2. **Fake-Sensor auf dem Pi:** in `main.py` `USE_FAKE_SENSOR = True` setzen. Der Fake spielt
   im 4-Sekunden-Takt: frei, Hindernis Mitte, links, rechts, alles blockiert, Sensor-Ausfall.
   Erwartet in der Konsole: `Move to LEFT/RIGHT/STOP`, beim Ausfall die Warnung mit YOLO-Fallback.
3. **Erst mit echtem Sensor:** Raster-Orientierung, Status-/Sigma-Werte bei realen Flächen,
   Boden-Fehlalarme, I2C-Takt, Tuning der Schwellwerte.

## Hardware-Check mit dem echten Sensor
Siehe `tools/sensor_check.py` (zeigt das 8x8-Raster live in cm). Zuerst `i2cdetect -y 1`
(Sensor muss als `29` erscheinen), dann das Skript, dann erst `main.py`.
