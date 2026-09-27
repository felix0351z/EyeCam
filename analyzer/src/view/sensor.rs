use bevy::color::palettes::css::{GRAY, RED};
use bevy::prelude::*;

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct SensorViewPlugin;
impl Plugin for SensorViewPlugin {
    fn build(&self, app: &mut App) {
        app.add_systems(Startup, setup);
    }
}


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
}



