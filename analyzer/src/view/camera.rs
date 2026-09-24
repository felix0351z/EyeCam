use bevy::asset::{Assets, Handle, RenderAssetUsages};
use bevy::image::Image;
use bevy::prelude::{Commands, Res, ResMut, Resource, Sprite};
use bevy::render::render_resource::{Extent3d, TextureDimension, TextureFormat};
use crate::backend::protocol::Message;
use crate::view::MessageReceiver;

/// EyeCam Kamera-Bild, welches bei jedem Frame aktualisiert wird.
#[derive(Resource)]
pub struct LiveImage(pub Handle<Image>);


/// Erstelle das Bild und bereite die Ansicht vor
pub fn setup_camera(
    mut commands: Commands,
    mut images: ResMut<Assets<Image>>, // Zentraler Bildspeicher von Bevy
) {

    let image = Image::new(
        Extent3d { width: 1, height: 1, depth_or_array_layers: 1 },
        TextureDimension::D2,
        vec![0, 0, 0, 255],
        TextureFormat::Rgba8UnormSrgb,
        RenderAssetUsages::default(),
    );

    // Erstelle ein neues Handle für das Bild
    let handle = images.add(image);

    // Erstelle die Sprite-Ansicht und übergebe ihm einen Handle
    commands.spawn(Sprite::from_image(handle.clone()));

    // Erstelle ein LiveImage, über welches dann das Bild geupdated werden kann.
    commands.insert_resource(LiveImage(handle));

}

pub fn render(
    receiver: Res<MessageReceiver>,
    live_image: Res<LiveImage>,
    mut images: ResMut<Assets<Image>>,
) {

    // Nehme nur das letzte Frame.
    // Der Analyzer sollte schneller als der RaspberryPi sein.
    let Some(message) = receiver.0.try_iter().last() else {
        return;
    };

    // Hole das aktuelle Live-Image aus dem Bildspeicher
    let Some(mut image) = images.get_mut(&live_image.0) else {
        return;
    };

    match message {
        Message::Yolo(yolo) => {
            // Yolo Message verarbeiten

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

