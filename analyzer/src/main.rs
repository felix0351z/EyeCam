use bevy::DefaultPlugins;
use bevy::prelude::App;
use bevy_egui::EguiPlugin;
use bevy_panorbit_camera::PanOrbitCameraPlugin;
use crate::receiver::ReceiverPlugin;
use crate::view::camera::CameraViewPlugin;
use crate::view::sensor::SensorViewPlugin;
use crate::view::ViewPlugin;

mod view;
mod backend;
mod receiver;

fn main() {
    App::new()
        .add_plugins((DefaultPlugins, EguiPlugin::default(), PanOrbitCameraPlugin))
        .add_plugins((ReceiverPlugin, ViewPlugin, CameraViewPlugin, SensorViewPlugin))
        .run();
}

