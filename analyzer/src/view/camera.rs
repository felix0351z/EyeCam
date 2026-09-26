use bevy::prelude::*;
use std::fs;
use bevy::asset::RenderAssetUsages;
use bevy::color::palettes::css::RED;
use bevy::prelude::FontSize::Px;
use bevy::render::render_resource::{Extent3d, TextureDimension, TextureFormat};
use bevy::sprite::Anchor;
use crate::receiver::{LatestYoloMessage, ReceiveSet};

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct CameraViewPlugin;
impl Plugin for CameraViewPlugin {
    fn build(&self, app: &mut App) {
        app
            .add_systems(Startup, setup)
            .add_systems(Update, (
                update_live_image,
                update_boxes,
                update_label.run_if(resource_changed::<LiveImage>)
            ).chain().after(ReceiveSet));
    }
}

// --------------------------------------
// Ressourcen
// --------------------------------------

/// Aktuelles Kamerabild von der EyeCam
///
/// Das Live-Image wird in `render` aktualisiert.
/// Außerdem enthält das Objekt alle Yolo-Detections, welche zu dem aktuellen Bild gehören.
/// Diese werden von `render_label` und `render_boxes` dargestellt.
#[derive(Resource)]
struct LiveImage {
    handle: Handle<Image>,
    detections: Vec<YoloDetection>,
}

struct YoloDetection {
    rect: Rect,
    confidence: f32,
    class_id: i32
}

/// Die aktuellen Klassennamen aus der coco.names-Datei.
/// Wird in `setup` initialisiert.
#[derive(Resource)]
struct ClassNames(Vec<String>);

// --------------------------------------
// Komponenten
// --------------------------------------


/// Marker-Objekt
/// um die Labels oberhalb der Boxen wiederzufinden.
///
/// Die Labels werden mit dem Marker gespawned
/// und können daher dann mit Query<Entity, With<BoxLabel>> wieder gefunden werden.
#[derive(Component)]
struct BoxLabel;


/// Marker-Objekt
/// für den einfachen Zugriff auf das aktuelle Sprite
///
/// Dieser Marker wird dafür in `setup` zusammen dem Sprite gespawned.
/// Beide haben so dieselbe Entity.
/// Das Holen des Sprites geht dann einfach via Single<&Sprite, With<LiveImageSprite>>
#[derive(Component)]
struct LiveImageSprite;


// --------------------------------------
// Systeme & Hilfsfunktionen
// --------------------------------------

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


/// Bereite die Kameraansicht vor.
///
/// Am Anfang wird das Sprite (Bild) gespawned sowie alle nötigen
/// Ressourcen und Komponenten initialisiert.
fn setup(
    mut commands: Commands,
    mut images: ResMut<Assets<Image>>, // Zentraler Bildspeicher von Bevy,
    mut gizmos_config: ResMut<GizmoConfigStore>
) {

    // 1. Erstelle das Sprite (Bild in Bevy), sowie das zugehörige Handle.

    let image = Image::new(
        Extent3d { width: 1, height: 1, depth_or_array_layers: 1 },
        TextureDimension::D2,
        vec![0, 0, 0, 255],
        TextureFormat::Rgba8UnormSrgb,
        RenderAssetUsages::default(),
    );

    let handle = images.add(image);
    commands.spawn((Sprite::from_image(handle.clone()), LiveImageSprite));

    // 2. Erstelle ein 'LiveImage' Objekt,
    // über welches das aktuelle Sprite aktualisiert werden kann.
    commands.insert_resource(LiveImage { handle, detections: Vec::new() });


    // 3. Lese die Klassennamen aus coco.names ein
    let coco_names = fs::read_to_string("assets/coco.names")
        .map(|it| it.lines().map(String::from).collect())
        .unwrap_or_else(|e| {
            warn!("coco.names konnten nicht eingelesen werden: {e}");
            Vec::new()
        });

    commands.insert_resource(ClassNames(coco_names));


    // 4. Konfiguriere die Breite der Gizmos-Boxen
    let (config, _) = gizmos_config.config_mut::<DefaultGizmoConfigGroup>();
    config.line.width = 3.0;
}

/// Aktualisiere die Boxen aus dem `LiveImage` als Gizmos.
fn update_boxes(
    mut gizmos: Gizmos,
    live_image: Res<LiveImage>,
    images: Res<Assets<Image>>,
    live_sprite: Single<(&Sprite, &GlobalTransform), With<LiveImageSprite>>,
) {
    let (sprite, transform) = *live_sprite;

    let Some(image) = images.get(&live_image.handle) else { return };
    let image_size = image.size_f32();

    for detection in &live_image.detections {
        // Render Boxes
        let a = image_to_world(detection.rect.min, image_size, sprite, transform);
        let b = image_to_world(detection.rect.max, image_size, sprite, transform);

        let world = Rect::from_corners(a, b);
        gizmos.rect_2d(
            Isometry2d::from_translation(world.center()),
            world.size(),
            RED
        );
    }
}

/// Aktualisiere die Labels oberhalb von den Boxen
fn update_label(
    mut commands: Commands,
    live_image: Res<LiveImage>,
    images: Res<Assets<Image>>,
    class_names: Res<ClassNames>,
    live_sprite: Single<(&Sprite, &GlobalTransform), With<LiveImageSprite>>,
    labels: Query<Entity, With<BoxLabel>>,
) {
    let (sprite, transform) = *live_sprite;

    // Despawne die alten Labels bevor die neuen gespawned werden
    for entity in &labels {
        commands.entity(entity).despawn();
    }

    let Some(image) = images.get(&live_image.handle) else { return };
    let image_size = image.size_f32();

    // Spawne Label für jede Detection
    for detection in &live_image.detections {
        let a = image_to_world(detection.rect.min, image_size, sprite, transform);

        // Lade Klassennamen aus Id
        let class_name = class_names.0
            .get(detection.class_id as usize)
            .map(String::as_str)
            .unwrap_or("?");

        // Spawne Label oberhalb der Box
        commands.spawn((
            BoxLabel,
            Text2d::new(format!("{class_name} {:.0}%", detection.confidence * 100.0)),
            TextFont { font_size: Px(16.0), ..default() },
            TextColor(RED.into()),
            Anchor::BOTTOM_LEFT,
            Transform::from_translation(a.extend(1.0)),
        ));
    }
}

/// Aktualisiere `LiveImage` inklusive Sprite.
/// Das aktuelle bzw. nächste Frame wird aus `LatestYoloMessage` heraus gelesen.
fn update_live_image(
    mut latest_yolo: ResMut<LatestYoloMessage>,
    mut live_image: ResMut<LiveImage>,
    mut images: ResMut<Assets<Image>>,
) {
    // Nur rendern, wenn seit dem letzten Frame eine neue Nachricht angekommen ist.
    let Some(yolo) = latest_yolo.0.take() else { return; };

    // Hole das aktuelle Live-Image aus dem Bildspeicher
    let Some(mut image) = images.get_mut(&live_image.handle) else { return; };

    // Aktualisiere das Bild
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

    // Aktualisiere die Detections, also Boxen, Confidences und ClassIds in dem LiveImage
    live_image.detections = yolo.boxes.chunks_exact(4)
        .zip(yolo.confidences)
        .zip(yolo.class_ids)
        .map(|((b, confidence), class_id)| {
            YoloDetection {
                rect: Rect::from_corners(Vec2::new(b[0], b[1]), Vec2::new(b[2], b[3])),
                confidence,
                class_id,
            }
        })
        .collect();
}
