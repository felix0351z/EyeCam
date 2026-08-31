# VL53L5CX Setup — Raspberry Pi 3 (frisch, ohne bestehende Umgebung)

## Vorbereitung

- [ ] Raspberry Pi 3 mit installiertem Raspberry Pi OS
- [ ] VL53L5CX Sensor bereitgelegt
- [ ] 4 Jumper-/Qwiic-Kabel bereitgelegt
- [ ] Internetverbindung auf dem Pi vorhanden

## Schritt 1 — Pi vorbereiten

- [ ] `sudo apt update && sudo apt full-upgrade -y`

## Schritt 2 — I2C aktivieren

- [ ] `sudo raspi-config` → Interface Options → I2C → aktivieren
- [ ] `sudo reboot`

## Schritt 3 — Sensor verkabeln

- [ ] Pi mit `sudo poweroff` ausschalten
- [ ] VCC/3.3V → Pin 1
- [ ] GND → Pin 6
- [ ] SDA → Pin 3 (GPIO2)
- [ ] SCL → Pin 5 (GPIO3)
- [ ] Pi wieder einschalten

## Schritt 4 — Verbindung prüfen

- [ ] `sudo apt install -y i2c-tools`
- [ ] `i2cdetect -y 1`
- [ ] Adresse `0x29` (oder ähnlich) erscheint in der Tabelle

## Schritt 5 — Python-Umgebung einrichten

- [ ] `python3 -m venv ~/tof-env`
- [ ] `source ~/tof-env/bin/activate`

## Schritt 6 — SparkFun-Bibliothek installieren

- [ ] `pip install --upgrade pip`
- [ ] `pip install sparkfun-qwiic-vl53l5cx`

## Schritt 7 — Testskript erstellen

- [ ] `nano ~/test_vl53l5cx.py` 
- [ ] [[Test_vl5315cx.py]]
## Schritt 8 — Testen

- [ ] `python3 ~/test_vl53l5cx.py`
- [ ] Sensor initialisiert erfolgreich
- [ ] 8x8-Raster mit Distanzwerten wird live angezeigt
- [ ] Werte ändern sich beim Bewegen der Hand vor dem Sensor
## Schritt 9 matplotlib(Live-Heatmap)

- [ ] source ~/tof-env/bin/activate
- [ ] pip install matplotlib
## schritt 9 Visualisierungs-skript erstellen

- [ ] nano ~/tof_visual.py -> [[tof_visual.py]]
- [ ] testen -> python3 ~/tof_visual.py

## Troubleshooting (falls nötig)

- [ ] Bei leerem `i2cdetect` → Kabel (SDA/SCL) prüfen, ggf. vertauscht
- [ ] Bei "Sensor nicht verbunden" → I2C aktiviert? Richtiger Bus (`-y 0` statt `-y 1` testen)
- [ ] Bei hängender Initialisierung → Stromversorgung prüfen (3.3V, nicht 5V)x

