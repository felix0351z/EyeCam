use bevy::prelude::*;
use bevy_egui::{EguiGlobalSettings, EguiPlugin, EguiPrimaryContextPass, PrimaryEguiContext};

mod view;
mod backend;

pub const APP_NAME: &'static str = "EyeCam Analyzer";

fn main() {
    App::new()
        .add_plugins((DefaultPlugins, EguiPlugin::default()))
        .init_resource::<view::ViewRects>()
        .init_resource::<view::LatestYoloMessage>()
        //.init_resource::<view::PlotData>()

        .add_systems(Startup, (setup_egui, setup_receiver, view::camera::setup_camera))
        .add_systems(EguiPrimaryContextPass, (view::ui_layout, view::update_viewports))
        .add_systems(Update, (view::receive_messages, 
                              view::camera::render, 
                              view::camera::render_boxes, 
                              view::camera::render_text).chain()
        )
        .run();
}


fn setup_receiver(
    mut commands: Commands
) {
    // Starte den TCP-Listener in einem neuen Background-Thread.
    // Die Kommunikation funktioniert mit einem Crossbeam-Channel, 
    // wobei der Receiver in der Ressource MessageReceiver gespeichert wird.
    
    let (tx, rx) = crossbeam_channel::bounded(2);
    commands.insert_resource(view::MessageReceiver(rx));
    
    backend::spawn_eyecam_receiver(tx);
}

fn setup_egui(
    mut commands: Commands, 
    mut egui_settings: ResMut<EguiGlobalSettings>
) {

    // egui an keine Kamera hängen, da es für diese eigene Viewports gibt.
    egui_settings.auto_create_primary_context = false;

    // Erstelle eine neue Kamera, für den EyeCam-Kamera Bereich
    commands.spawn((Camera2d, Camera { order: 0, ..default() }, view::CameraForViewCamera));

    
    // Eigene Kamera nur für egui, über das ganze Fenster, zuletzt gerendert.
    commands.spawn((
        Camera2d,
        Camera { order: 2, clear_color: ClearColorConfig::None, ..default() },
        PrimaryEguiContext,
        bevy::camera::visibility::RenderLayers::none(),
    ));
}