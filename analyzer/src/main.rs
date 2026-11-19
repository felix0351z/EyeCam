use bevy::DefaultPlugins;
use bevy::prelude::App;
use bevy_egui::EguiPlugin;
use crate::receiver::ReceiverPlugin;
use crate::view::camera::CameraViewPlugin;
use crate::view::graph::GraphViewPlugin;
use crate::view::move_signal::MoveSignalViewPlugin;
use crate::view::sensor2d::SensorView2Plugin;
use crate::view::ViewPlugin;

mod view;
mod backend;
mod receiver;
mod logger;

fn main() {
    App::new()
        .add_plugins((DefaultPlugins, EguiPlugin::default()))
        .add_plugins((ReceiverPlugin, ViewPlugin, CameraViewPlugin, SensorView2Plugin, GraphViewPlugin, MoveSignalViewPlugin))
        .run();
}

