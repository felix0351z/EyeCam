use crate::view::AnalyzerView;
use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiPlugin, EguiPrimaryContextPass};
use egui::{LayerId, Ui, UiBuilder};

mod view;
mod viewmodel;
mod backend;

pub const APP_NAME: &'static str = "EyeCam Analyzer";

fn main() {
    
    

    //TODO: Struktur reinbringen, vtl. nochmal von mvvm zu etwas anderem wechseln.
    //TODO: ChatGPT wegen der bildübertragung fragen hinzu bevy/egui

    //TODO: 1. Empfangen Bilddaten - Schnittstelle implementieren => TCP mit Packet JPD Codierung für beste performance probiern
    //TODO: 2. Daten verarbeiten - Boxen zeichnen etc.
    //TODO: 3. Darstellen in egui. Bild wird gezeichnet, boxen obendrauf mit bevy (nicht in bild)

    App::new()
        .add_plugins(DefaultPlugins)
        .add_plugins(EguiPlugin::default())
        .add_systems(Startup, setup_camera_system)
        .add_systems(EguiPrimaryContextPass, ui_loop)
        .add_systems(Startup, setup_analyzer)
        .run();
}


fn setup_camera_system(mut commands: Commands) {
    // Setup bevy camera
    commands.spawn(Camera2d);
}

fn setup_analyzer(world: &mut World) {
    world.insert_non_send(AnalyzerView::default());
}

fn ui_loop(mut contexts: EguiContexts, mut analyzer: NonSendMut<AnalyzerView>) -> Result {
    // Setup egui ui

    let ctx = contexts.ctx_mut()?;
    let mut viewport_ui = Ui::new(
        ctx.clone(),
        "viewport".into(),
        UiBuilder::new()
            .layer_id(LayerId::background())
            .max_rect(ctx.viewport_rect()),
    );

    analyzer.ui_bevy(&mut viewport_ui);
    Ok(())
}