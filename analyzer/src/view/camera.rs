use bevy::asset::{Assets, Handle, RenderAssetUsages};
use bevy::color::palettes::css::RED;
use bevy::image::Image;
use bevy::math::{Isometry2d, Rect};
use bevy::prelude::{Commands, DefaultGizmoConfigGroup, GizmoConfigStore, Gizmos, GlobalTransform, Query, Res, ResMut, Resource, Sprite, Vec2};
use bevy::render::render_resource::{Extent3d, TextureDimension, TextureFormat};
use crate::view::LatestYoloMessage;

/// EyeCam Kamera-Bild, welches bei jedem Frame aktualisiert wird.
#[derive(Resource)]
pub struct LiveImage {
    pub handle: Handle<Image>,
    /// Erkannte Boxen in Bildpixeln (Ursprung oben links, y nach unten)
    pub boxes: Vec<Rect>
}


/// Rechne Box-Koordinaten von dem Python-Sender in das Bevy-Koordinatensystem um.
///
/// In Python beginnt der Ursprung (0, 0) in der oberen linken Ecke und Y geht nach unten
/// In Bevy liegt der Ursprung in der Mitte und Y geht nach oben
/// Daher müssen die Koordinaten umgerechnet werden.
///
/// Zudem muss, falls das Sprite eine andere Größe wie die Pixelskalierung hat, diese Skalierung
/// noch umberechnet werden.
fn image_to_world(p: Vec2, image_size: Vec2, sprite: &Sprite, transform: &GlobalTransform) -> Vec2 {
    let display_size = sprite.custom_size.unwrap_or(image_size);
    let factor = display_size / image_size;

    let local = Vec2::new(
        (p.x - image_size.x / 2.0) * factor.x,
        (image_size.y / 2.0 - p.y) * factor.y,
    );

    transform.transform_point(local.extend(0.0)).truncate()
}



/// Erstelle das Bild und bereite die Ansicht vor
pub fn setup_camera(
    mut commands: Commands,
    mut images: ResMut<Assets<Image>>, // Zentraler Bildspeicher von Bevy,
    mut gizmos_config: ResMut<GizmoConfigStore>
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
    commands.insert_resource(LiveImage {
        handle,
        boxes: Vec::new(),
    });

    // Konfiguriere die Breite der Gizmos-Boxen
    let (config, _) = gizmos_config.config_mut::<DefaultGizmoConfigGroup>();
    config.line.width = 3.0;

}

pub fn render_boxes(
    mut gizmos: Gizmos,
    live_image: Res<LiveImage>,
    images: Res<Assets<Image>>,
    sprites: Query<(&Sprite, &GlobalTransform)>,
) {
    let Some(image) = images.get(&live_image.handle) else {
        return
    };

    let image_size = image.size_f32();

    for (sprite, transform) in &sprites {
        // Nur das Sprite, das dein Live-Bild anzeigt
        if sprite.image != live_image.handle {
            continue;
        }

        for rect in &live_image.boxes {
            let a = image_to_world(rect.min, image_size, sprite, transform);
            let b = image_to_world(rect.max, image_size, sprite, transform);

            let world = Rect::from_corners(a, b);
            gizmos.rect_2d(
                Isometry2d::from_translation(world.center()),
                world.size(),
                RED
            );
        }
    }
}


pub fn render(
    mut latest_yolo: ResMut<LatestYoloMessage>,
    mut live_image: ResMut<LiveImage>,
    mut images: ResMut<Assets<Image>>,
) {
    // Nur verarbeiten, wenn seit dem letzten Frame eine neue Nachricht angekommen ist.
    let Some(yolo) = latest_yolo.0.take() else { return; };

    // Hole das aktuelle Live-Image aus dem Bildspeicher
    let Some(mut image) = images.get_mut(&live_image.handle) else { return; };

    let jpeg = yolo.jpeg;
    let size = image.texture_descriptor.size;

    let new_width = jpeg.width as u32;
    let new_height = jpeg.height as u32;


    if size.width == new_width && size.height == new_height {
        // Gleiche Größe, nur Pixel tauschen.
        image.data = Some(jpeg.data);
    } else {
        // Neue Größe, Image neu anlegen.
        *image = Image::new(
            Extent3d { width: new_width, height: new_height, depth_or_array_layers: 1 },
            TextureDimension::D2,
            jpeg.data,
            TextureFormat::Rgba8UnormSrgb,
            RenderAssetUsages::default(),
        );
    }

    // Das abgeflachte Array hat 4 Box-Koordinaten pro Box: x1, y1, x2, y2 (Bildpixel)
    live_image.boxes = yolo.boxes
        .chunks_exact(4)
        .map(|b| Rect::from_corners(Vec2::new(b[0], b[1]), Vec2::new(b[2], b[3])))
        .collect();
}
