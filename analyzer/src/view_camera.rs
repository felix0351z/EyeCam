use bevy::asset::RenderAssetUsages;
use bevy::prelude::{Assets, Handle, Image, Res, ResMut, Resource};
use bevy::render::render_resource::{Extent3d, TextureDimension, TextureFormat};
use crate::backend::protocol::Message;
use crate::view::CameraReceiver;



#[derive(Resource)]
pub struct LiveImage(pub Handle<Image>);


pub fn apply_latest_frame(
    receiver: Res<CameraReceiver>,
    live_image: Res<LiveImage>,
    mut images: ResMut<Assets<Image>>,
) {

    let Some(message) = receiver.0.try_iter().last() else {
        return;
    };
    let Some(mut image) = images.get_mut(&live_image.0) else {
        return;
    };

    match message {
        Message::Yolo(yolo) => {
            let jpeg = yolo.jpeg;
            let size = image.texture_descriptor.size;

            let newWidth = jpeg.width as u32;
            let newHeight = jpeg.height as u32;


            if size.width == newWidth && size.height == newHeight {
                // Gleiche Größe: nur die Pixel austauschen.
                image.data = Some(jpeg.data);
            } else {
                // Neue Größe: Image neu anlegen (gleicher Handle, Anzeigen bleiben verbunden).
                *image = Image::new(
                    Extent3d { width: newWidth, height: newHeight, depth_or_array_layers: 1 },
                    TextureDimension::D2,
                    jpeg.data,
                    TextureFormat::Rgba8UnormSrgb,
                    // Main + Render World, damit wir die Daten später ändern dürfen.
                    RenderAssetUsages::default(),
                );
            }



        }
        Message::Graph(_) => {}
    }



}

