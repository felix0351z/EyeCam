


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
commands.spawn((PointLight::default(), Transform::from_xyz(4.0, 8.0, 4.0)));
*/

/*
// 3D-Punkte-Ansicht: darf nicht clearen, sonst wird die 2D-Ansicht übermalt.
commands.spawn((
    Camera3d::default(),
    Camera { order: 1, clear_color: ClearColorConfig::None, ..default() },
    Transform::from_xyz(4.0, 3.0, 6.0).looking_at(Vec3::ZERO, Vec3::Y),
    view::ViewCam3d,
));
*/
