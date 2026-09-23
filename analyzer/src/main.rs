use bevy::asset::RenderAssetUsages;
use bevy::prelude::*;
use bevy::render::render_resource::{Extent3d, TextureDimension, TextureFormat};
use bevy_egui::{EguiGlobalSettings, EguiPlugin, EguiPrimaryContextPass, PrimaryEguiContext};
use crate::backend::spawn_eyecam_reader;
use crate::view_camera::LiveImage;

mod view;
mod backend;
mod view_camera;

pub const APP_NAME: &'static str = "EyeCam Analyzer";

fn main() {

    App::new()
        .add_plugins((DefaultPlugins, EguiPlugin::default()))
        .init_resource::<view::ViewRects>()
        //.init_resource::<view::PlotData>()

        .add_systems(Startup, (setup_camera_system, setup_scene))
        .add_systems(EguiPrimaryContextPass, (view::ui_layout, view::update_viewports))
        .add_systems(Update, view_camera::apply_latest_frame)
        .run();
}


fn setup_camera_system(mut commands: Commands, mut egui_settings: ResMut<EguiGlobalSettings>) {

    // egui an keine Kamera hängen, da es für diese eigene Viewports gibt.
    egui_settings.auto_create_primary_context = false;

    // 2D-Bild-Ansicht: rendert zuerst und löscht den gesamten Hintergrund.
    commands.spawn((Camera2d, Camera { order: 0, ..default() }, view::ViewEyecamCamera));

    /*
    // 3D-Punkte-Ansicht: darf nicht clearen, sonst wird die 2D-Ansicht übermalt.
    commands.spawn((
        Camera3d::default(),
        Camera { order: 1, clear_color: ClearColorConfig::None, ..default() },
        Transform::from_xyz(4.0, 3.0, 6.0).looking_at(Vec3::ZERO, Vec3::Y),
        view::ViewCam3d,
    ));
    */

    // Eigene Kamera nur für egui, über das ganze Fenster, zuletzt gerendert.
    commands.spawn((
        Camera2d,
        Camera { order: 2, clear_color: ClearColorConfig::None, ..default() },
        PrimaryEguiContext,
        bevy::camera::visibility::RenderLayers::none(),
    ));
}

fn setup_scene(mut commands: Commands,
               mut images: ResMut<Assets<Image>>,
) {
    // 2D: Bild als Sprite (liegt unter assets/bild.png)
    //commands.spawn(Sprite::from_image(asset_server.load("bild.png")));


    let image = Image::new(
        Extent3d { width: 1, height: 1, depth_or_array_layers: 1 },
        TextureDimension::D2,
        vec![0, 0, 0, 255],
        TextureFormat::Rgba8UnormSrgb,
        // Main + Render World, damit wir die Daten später ändern dürfen.
        RenderAssetUsages::default(),
    );
    let handle = images.add(image);

    // In der 2D-Ansicht anzeigen. Das Sprite aktualisiert sich automatisch mit.
    //commands.spawn(Sprite::from_image(handle.clone()));
    commands.insert_resource(LiveImage(handle));


    let (tx, rx) = crossbeam_channel::bounded(2);
    commands.insert_resource(view::CameraReceiver(rx));
    spawn_eyecam_reader(tx);

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
}