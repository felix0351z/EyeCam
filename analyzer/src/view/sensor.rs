use bevy::color::palettes::css::{DARK_GRAY, GRAY, LIME, RED};
use bevy::prelude::*;
use std::f32::consts::FRAC_PI_4;
use crate::receiver::{LatestSensorMessage, ReceiveSet};

/// Sichtfeld des VL53L5CX (horizontal und vertikal), 45°.
const FOV: f32 = FRAC_PI_4;

/// Maximale Anzahl an Zonen (8x8-Modus).
const MAX_ZONES: usize = 64;

/// `target_status`-Codes, welche laut ST eine gültige Messung bedeuten.
const VALID_TARGET_STATUS: [u8; 2] = [5, 9];

/// Länge der Sichtfeld-Pyramide in Metern.
const FOV_GIZMO_LENGTH: f32 = 0.5;

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct SensorViewPlugin;
impl Plugin for SensorViewPlugin {
    fn build(&self, app: &mut App) {
        app
            .add_systems(Startup, setup)
            .add_systems(Update, (update_zones.after(ReceiveSet), draw_fov));
    }
}

// --------------------------------------
// Komponenten
// --------------------------------------

/// Marker für den Messpunkt einer Sensorzone.
///
/// Enthält den Index der Zone in der `SensorMessage`.
/// Alle Zonen werden in `setup` gespawned und in `update_zones` nur noch verschoben.
#[derive(Component)]
struct SensorZone(usize);


// --------------------------------------
// Systeme und Hilfsfunktionen
// --------------------------------------

/// Baue die 3D-Szene für den VL53L5CX Sensor auf.
///
/// Der Sensor steht im Ursprung und blickt nach vorne entlang -Z (Bevy-Standard).
/// Einheiten sind Meter.
fn setup(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    // Licht
    commands.spawn((
        DirectionalLight::default(),
        // Licht von schräg vorne oben, damit die Vorderseite mit der Linse beleuchtet ist.
        Transform::from_xyz(1.0, 2.0, -1.5).looking_at(Vec3::ZERO, Vec3::Y),
    ));

    // Sensor-Gehäuse als aufrecht stehender, flacher Quader
    commands.spawn((
        Mesh3d(meshes.add(Cuboid::new(0.1, 0.1, 0.04))),
        MeshMaterial3d(materials.add(Color::from(GRAY))),
        Transform::IDENTITY,
    ));

    // Linse auf der Vorderseite (-Z), damit die Blickrichtung erkennbar ist.
    // Der Zylinder steht standardmäßig entlang Y und wird daher um X gekippt.
    commands.spawn((
        Mesh3d(meshes.add(Cylinder::new(0.02, 0.01))),
        MeshMaterial3d(materials.add(Color::from(RED))),
        Transform::from_xyz(0.0, 0.0, -0.025)
            .with_rotation(Quat::from_rotation_x(std::f32::consts::FRAC_PI_2)),
    ));

    // Messpunkte für alle Zonen, anfangs versteckt.
    // Mesh und Material werden von allen Zonen geteilt.
    let zone_mesh = meshes.add(Sphere::new(0.015));
    let zone_material = materials.add(Color::from(LIME));
    for index in 0..MAX_ZONES {
        commands.spawn((
            SensorZone(index),
            Mesh3d(zone_mesh.clone()),
            MeshMaterial3d(zone_material.clone()),
            Transform::IDENTITY,
            Visibility::Hidden,
        ));
    }
}

/// Rechne eine Sensorzone und ihre Distanz in eine Position im Bevy-Koordinatensystem um.
///
/// Die Zonen liegen zeilenweise im Array, Zone 0 wird oben links angenommen.
/// Die Distanz wird als Tiefe senkrecht zur Sensorfläche (entlang -Z) interpretiert.
fn zone_to_world(index: usize, resolution: usize, distance_mm: i16) -> Vec3 {
    let row = index / resolution;
    let col = index % resolution;

    // Winkel zur Mitte der Zone
    let zone_angle = FOV / resolution as f32;
    let angle_x = (col as f32 + 0.5) * zone_angle - FOV / 2.0;
    let angle_y = FOV / 2.0 - (row as f32 + 0.5) * zone_angle;

    let depth = distance_mm as f32 / 1000.0;
    Vec3::new(angle_x.tan() * depth, angle_y.tan() * depth, -depth)
}

/// Aktualisiere die Messpunkte aus der neusten Sensor-Nachricht.
///
/// Zonen ohne gültige Messung werden versteckt.
fn update_zones(
    mut latest_sensor: ResMut<LatestSensorMessage>,
    mut zones: Query<(&SensorZone, &mut Transform, &mut Visibility)>,
) {
    // Nur aktualisieren, wenn seit dem letzten Frame eine neue Nachricht angekommen ist.
    let Some(sensor) = latest_sensor.0.take() else { return };

    // 16 Zonen -> 4x4, 64 Zonen -> 8x8
    let resolution = (sensor.distance_mm.len() as f32).sqrt() as usize;

    for (zone, mut transform, mut visibility) in &mut zones {
        let point = sensor.distance_mm.get(zone.0)
            .zip(sensor.target_status.get(zone.0))
            .filter(|&(_, &status)| VALID_TARGET_STATUS.contains(&status))
            .map(|(&distance, _)| zone_to_world(zone.0, resolution, distance));

        match point {
            Some(point) => {
                transform.translation = point;
                *visibility = Visibility::Inherited;
            }
            None => *visibility = Visibility::Hidden,
        }
    }
}

/// Zeichne das Sichtfeld des Sensors als Pyramide.
fn draw_fov(mut gizmos: Gizmos) {
    let half = (FOV / 2.0).tan() * FOV_GIZMO_LENGTH;
    let corners = [
        Vec3::new(-half, half, -FOV_GIZMO_LENGTH),
        Vec3::new(half, half, -FOV_GIZMO_LENGTH),
        Vec3::new(half, -half, -FOV_GIZMO_LENGTH),
        Vec3::new(-half, -half, -FOV_GIZMO_LENGTH),
    ];

    for corner in corners {
        gizmos.line(Vec3::ZERO, corner, DARK_GRAY);
    }
    //gizmos.linestrip(corners.into_iter().chain([corners[0]]), DARK_GRAY);
}
