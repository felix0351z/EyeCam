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


fn setup(
    mut commands: Commands


) {
    commands.spawn((PointLight::default(), Transform::from_xyz(4.0, 8.0, 4.0)));

}


// 3D: ein paar Punkte als kleine Kugeln
/*
let mesh = meshes.add(Sphere::new(0.05));
let material = materials.add(StandardMaterial::default());
for i in 0..50 {
    let t = i as f32 * 0.3;
    commands.spawn((
        Mesh3d(mesh.clone()),
        MeshMaterial3d(material.clone()),
        Transform::from_xyz(t.cos() * 2.0, t * 0.1, t.sin() * 2.0),
    ));
}
*/

