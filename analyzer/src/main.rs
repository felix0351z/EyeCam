use bevy::DefaultPlugins;
use bevy::prelude::App;
use bevy_egui::EguiPlugin;
use crate::receiver::ReceiverPlugin;
use crate::view::camera::CameraViewPlugin;
use crate::view::ViewPlugin;

mod view;
mod backend;
mod receiver;

fn main() {
    App::new()
        .add_plugins((DefaultPlugins, EguiPlugin::default()))
        .add_plugins((ReceiverPlugin, ViewPlugin, CameraViewPlugin))
        .run();
}

