use bevy::camera::visibility::RenderLayers;
use bevy::color::palettes::css::DARK_GRAY;
use bevy::prelude::*;
use bevy::prelude::FontSize::Px;
use crate::receiver::{LatestSensorMessage, ReceiveSet};

/// RenderLayer der Sensoransicht.
/// Trennt die Sensor-Sprites von der Kameraansicht, welche auf Layer 0 rendert.
pub const SENSOR_LAYER: usize = 1;

/// Kantenlänge des gesamten Rasters in Welteinheiten.
/// Die Kamera skaliert so, dass genau diese Fläche sichtbar ist.
pub const GRID_SIZE: f32 = 800.0;

/// Maximale Auflösung des Sensors (8x8-Modus).
const MAX_RESOLUTION: usize = 8;

/// Maximale Anzahl an Zonen (8x8-Modus).
const MAX_ZONES: usize = MAX_RESOLUTION * MAX_RESOLUTION;

/// Abstand zwischen zwei Zonen in Welteinheiten.
const GAP: f32 = 4.0;

/// `target_status`-Codes, welche laut ST eine gültige Messung bedeuten.
const SENSOR_VALID_STATUS: [u8; 2] = [5, 9];

/// Distanz, ab welcher die Farbe nicht mehr weiter verläuft.
const SENSOR_MAX_DISTANCE_MM: f32 = 4000.0;


// --------------------------------------
// Plugin Setup
// --------------------------------------

pub struct SensorView2Plugin;
impl Plugin for SensorView2Plugin {
    fn build(&self, app: &mut App) {
        app
            .add_systems(Startup, setup)
            .add_systems(Update, update_zones.after(ReceiveSet));
    }
}

// --------------------------------------
// Komponenten
// --------------------------------------

/// Marker für eine Sensorzone.
///
/// Enthält den Index der Zone in der `SensorMessage`.
/// Sitzt sowohl auf dem Sprite als auch auf dessen Text-Kind,
/// damit beide in `update_zones` über den Index gefunden werden.
#[derive(Component)]
struct SensorZone(usize);


// --------------------------------------
// Systeme und Hilfsfunktionen
// --------------------------------------

/// Spawne für jede Zone ein Sprite mit einem Text als Kind.
///
/// Bis zur ersten Sensor-Nachricht wird ein graues 8x8-Raster ohne Messwerte angezeigt.
fn setup(mut commands: Commands) {
    let cell = GRID_SIZE / MAX_RESOLUTION as f32;

    for index in 0..MAX_ZONES {
        commands.spawn((
            SensorZone(index),
            Sprite::from_color(DARK_GRAY, Vec2::splat(cell - GAP)),
            Transform::from_translation(zone_to_grid(index, MAX_RESOLUTION).extend(0.0)),
            RenderLayers::layer(SENSOR_LAYER),
            children![(
                SensorZone(index),
                Text2d::new("-"),
                TextFont { font_size: Px(22.0), ..default() },
                TextColor(Color::BLACK),
                // Knapp vor dem Sprite, damit der Text nicht verdeckt wird.
                Transform::from_xyz(0.0, 0.0, 1.0),
                // RenderLayers wird nicht vererbt und muss daher auch hier gesetzt werden.
                RenderLayers::layer(SENSOR_LAYER),
            )],
        ));
    }
}

/// Mittelpunkt einer Zone im Raster.
///
/// Die Zonen liegen zeilenweise im Array, Zone 0 wird oben links angenommen.
/// In Bevy zeigt Y nach oben, daher wird die Zeile umgedreht.
fn zone_to_grid(index: usize, resolution: usize) -> Vec2 {
    let cell = GRID_SIZE / resolution as f32;
    let row = index / resolution;
    let col = index % resolution;

    Vec2::new(
        (col as f32 + 0.5) * cell - GRID_SIZE / 2.0,
        GRID_SIZE / 2.0 - (row as f32 + 0.5) * cell,
    )
}

/// Farbe einer Distanz: nah = rot, fern = blau.
fn distance_to_color(distance_mm: i16) -> Color {
    let t = (distance_mm as f32 / SENSOR_MAX_DISTANCE_MM).clamp(0.0, 1.0);
    Color::hsl(t * 240.0, 0.9, 0.55)
}

/// Distanz einer Zone, falls die Messung gültig ist.
fn valid_distance(distance_mm: &[i16], target_status: &[u8], index: usize) -> Option<i16> {
    distance_mm.get(index)
        .zip(target_status.get(index))
        .filter(|&(_, status)| SENSOR_VALID_STATUS.contains(status))
        .map(|(&distance, _)| distance)
}

/// Aktualisiere Position, Größe, Farbe und Text aller Zonen aus der neusten Sensor-Nachricht.
///
/// Zonen ohne gültige Messung werden grau und mit `NO_DISTANCE_TEXT` dargestellt.
fn update_zones(
    mut latest_sensor: ResMut<LatestSensorMessage>,
    mut zones: Query<(&SensorZone, &mut Sprite, &mut Transform, &mut Visibility)>,
    mut labels: Query<(&SensorZone, &mut Text2d)>,
) {
    // Nur aktualisieren, wenn seit dem letzten Frame eine neue Nachricht angekommen ist.
    let Some(sensor) = latest_sensor.0.take() else { return };

    // 16 Zonen -> 4x4, 64 Zonen -> 8x8
    let zone_count = sensor.distance_mm.len();
    let resolution = (zone_count as f32).sqrt() as usize;
    if resolution == 0 { return; }
    let cell = GRID_SIZE / resolution as f32;

    for (zone, mut sprite, mut transform, mut visibility) in &mut zones {
        // Im 4x4-Modus werden die übrigen Zonen nicht gebraucht.
        if zone.0 >= zone_count {
            *visibility = Visibility::Hidden;
            continue;
        }

        transform.translation = zone_to_grid(zone.0, resolution).extend(0.0);
        sprite.custom_size = Some(Vec2::splat(cell - GAP));
        sprite.color = valid_distance(&sensor.distance_mm, &sensor.target_status, zone.0)
            .map(distance_to_color)
            .unwrap_or(DARK_GRAY.into());
        *visibility = Visibility::Inherited;
    }

    for (zone, mut text) in &mut labels {
        text.0 = valid_distance(&sensor.distance_mm, &sensor.target_status, zone.0)
            .map(|distance| distance.to_string())
            .unwrap_or_else(|| "-".to_string());
    }
}
