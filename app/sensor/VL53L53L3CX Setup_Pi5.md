# VL53L5CX Setup — Raspberry Pi 5 (bestehende conda-Umgebung `ultralytics-env`)

## Vorbereitung

- [ ] VL53L5CX Sensor bereitgelegt
- [ ] 4 Jumper-/Qwiic-Kabel bereitgelegt
- [ ] Pi 5 läuft bereits mit funktionierender `ultralytics-env` (Kamera, YOLO, NCNN)

## Schritt 1 — I2C aktivieren 

- [ ] `sudo raspi-config` → Interface Options → I2C → aktivieren
- [ ] `sudo reboot`

## Schritt 2 — Sensor verkabeln

- [ ] Pi mit `sudo poweroff` ausschalten
- [ ] VCC/3.3V → Pin 1
- [ ] GND → Pin 6
- [ ] SDA → Pin 3 (GPIO2)
- [ ] SCL → Pin 5 (GPIO3)
- [ ] Pi wieder einschalten

## Schritt 3 — Verbindung prüfen

- [ ] `sudo apt install -y i2c-tools`
- [ ] `i2cdetect -y 1`
- [ ] Adresse `0x29` (oder ähnlich) erscheint in der Tabelle

## Schritt 4 — Bibliothek in bestehende Umgebung installieren

- [ ] `conda activate ultralytics-env`
- [ ] `pip install sparkfun-qwiic-vl53l5cx`
- [ ] Bei NVIDIA/CUDA-Paketen während der Installation → abbrechen und `--no-deps` verwenden (bekanntes Muster aus dem Projekt)

## Schritt 5 — Testskript erstellen

- [ ] `nano ~/hausmesse/test_vl53l5cx.py` 
- [ ] [[Test_vl5315cx.py]]
## Schritt 6 — Testen

- [ ] `conda activate ultralytics-env` (falls nicht schon aktiv)
- [ ] `python3 ~/hausmesse/test_vl53l5cx.py`
- [ ] Sensor initialisiert erfolgreich
- [ ] 8x8-Raster mit Distanzwerten wird live angezeigt
- [ ] Werte ändern sich beim Bewegen der Hand vor dem Sensor
## Schritt 7 matplotlib(Live-Heatmap)

- [ ] pip install matplotlib
## schritt 8 Visualisierungs-skript erstellen

- [ ] nano ~/tof_visual.py -> [[tof_visual.py]]
- [ ] testen -> python3 ~/tof_visual.py

## Troubleshooting (falls nötig)

- [ ] Bei leerem `i2cdetect` → Kabel (SDA/SCL) prüfen, ggf. vertauscht
- [ ] Bei "Sensor nicht verbunden" → I2C aktiviert? Richtiger Bus (`-y 0` statt `-y 1` testen)
- [ ] Bei hängender Initialisierung → Stromversorgung prüfen (3.3V, nicht 5V)x

## Schritt 7 — Integration ins Projekt (nächster Schritt nach erfolgreichem Test)

- [ ] Links/Rechts-Verarbeitung der Distanzdaten implementieren
- [ ] Verbindung zum ESP32 (WLAN) für Vibrationsmotor-Ansteuerung aufbauen
- [ ] Optional: Protobuf-Kommunikation zur Rust-Analyzer-App einrichten

## Troubleshooting (falls nötig)

- [ ] Bei leerem `i2cdetect` → Kabel (SDA/SCL) prüfen, ggf. vertauscht
- [ ] Bei "Sensor nicht verbunden" → I2C aktiviert? Richtiger Bus (`-y 0` statt `-y 1` testen)
- [ ] Bei hängender Initialisierung → Stromversorgung prüfen (3.3V, nicht 5V)
- [ ] Bei Import-Fehlern in conda → prüfen ob `.pth`-Link auf `/usr/lib/python3/dist-packages` noch korrekt ist (bekanntes Problem aus dem Kamera-Setup)