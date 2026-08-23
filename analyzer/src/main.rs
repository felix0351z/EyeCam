use crate::view::AnalyzerView;
use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiPlugin, EguiPrimaryContextPass};
use egui::{LayerId, Ui, UiBuilder};

mod view;
mod viewmodel;
mod reader;

pub const APP_NAME: &'static str = "EyeCam Analyzer";

fn main() {

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1920.0, 1080.0]),
        ..Default::default()
    };

    eframe::run_native(APP_NAME, options, Box::new(|creation_context| {
        creation_context.egui_ctx.set_theme(egui::Theme::Dark);
        Ok(Box::<view::AnalyzerView>::default())
    })).expect("Failed to run app");

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