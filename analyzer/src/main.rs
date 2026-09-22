use bevy::prelude::*;
use bevy_egui::{EguiGlobalSettings, EguiPlugin, EguiPrimaryContextPass, PrimaryEguiContext};

mod view;
mod backend;

pub const APP_NAME: &'static str = "EyeCam Analyzer";

fn main() {
    
    

    //TODO: Struktur reinbringen, vtl. nochmal von mvvm zu etwas anderem wechseln.
    //TODO: ChatGPT wegen der bildübertragung fragen hinzu bevy/egui

    //TODO: 1. Empfangen Bilddaten - Schnittstelle implementieren => TCP mit Packet JPD Codierung für beste performance probiern
    //TODO: 2. Daten verarbeiten - Boxen zeichnen etc.
    //TODO: 3. Darstellen in egui. Bild wird gezeichnet, boxen obendrauf mit bevy (nicht in bild)

    App::new()
        .add_plugins((DefaultPlugins, EguiPlugin::default()))
        .init_resource::<view::ViewRects>()
        .init_resource::<view::PlotData>()

        .add_systems(Startup, (setup_camera_system, setup_scene))
        .add_systems(EguiPrimaryContextPass, view::ui_layout)
        .run();
}


fn setup_camera_system(mut commands: Commands, mut egui_settings: ResMut<EguiGlobalSettings>) {

    // egui an keine Kamera hängen, da es für diese eigene Viewports gibt.
    egui_settings.auto_create_primary_context = false;

    // 2D-Bild-Ansicht: rendert zuerst und löscht den gesamten Hintergrund.
    commands.spawn((Camera2d, Camera { order: 0, ..default() }, view::View2dCamera));


    // 3D-Punkte-Ansicht: darf nicht clearen, sonst wird die 2D-Ansicht übermalt.
    commands.spawn((
        Camera3d::default(),
        Camera { order: 1, clear_color: ClearColorConfig::None, ..default() },
        Transform::from_xyz(4.0, 3.0, 6.0).looking_at(Vec3::ZERO, Vec3::Y),
        view::View3dCamera,
    ));

    // Eigene Kamera nur für egui, über das ganze Fenster, zuletzt gerendert.
    commands.spawn((
        Camera2d,
        Camera { order: 2, clear_color: ClearColorConfig::None, ..default() },
        PrimaryEguiContext,
        bevy::camera::visibility::RenderLayers::none(),
    ));
}

fn setup_scene(mut commands: Commands,
               asset_server: Res<AssetServer>,
               mut meshes: ResMut<Assets<Mesh>>,
               mut materials: ResMut<Assets<StandardMaterial>>
) {
    // 2D: Bild als Sprite (liegt unter assets/bild.png)
    commands.spawn(Sprite::from_image(asset_server.load("bild.png")));

    // 3D: ein paar Punkte als kleine Kugeln
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
}