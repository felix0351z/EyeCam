pub mod camera;
pub mod sensor2d;

use bevy::camera::{CameraOutputMode, Hdr, ScalingMode, Viewport};
use bevy::camera::visibility::RenderLayers;
use bevy::render::render_resource::BlendState;
use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiGlobalSettings, EguiPrimaryContextPass, PrimaryEguiContext};

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct ViewPlugin;
impl Plugin for ViewPlugin {
    fn build(&self, app: &mut App) {
        app
            .init_resource::<ViewRects>()
            .add_systems(Startup, setup)
            .add_systems(EguiPrimaryContextPass, (ui_layout, update_viewports));
    }
}

// --------------------------------------
// Ressourcen und Komponenten
// --------------------------------------

/// Ressource, welche die Rects für die Bevy-Views beinhaltet.
/// Bevy nutzt diese egui-Rects und zeichnet seinen Inhalt hinein.
#[derive(Resource)]
struct ViewRects {
    view_camera: egui::Rect,
    view_sensor: egui::Rect
}

impl Default for ViewRects {
    fn default() -> Self {
        ViewRects {
            view_camera: egui::Rect::ZERO,
            view_sensor: egui::Rect::ZERO,
        }
    }
}

/// Bevy-Kamera für die linke Seite des Fensters,
/// in welchem die EyeCam Camera in `view::camera`. dargestellt werden soll.
#[derive(Component)]
struct CameraForViewCamera;

/// Bevy-Kamera für die rechte Seite des Fensters,
/// in welchem der VL53L5CX Sensor in `view::sensor2d`. dargestellt werden soll.
#[derive(Component)]
struct CameraForViewSensor;


// --------------------------------------
// Systeme und Hilfsfunktionen
// --------------------------------------


/// Initialisiere das Bevy-Egui System
/// und erstelle eine Kamera für jede UI-Ansicht.
fn setup(mut commands: Commands, mut egui_settings: ResMut<EguiGlobalSettings>) {
    // egui an keine Kamera hängen, da es für diese eigene Viewports gibt.
    egui_settings.auto_create_primary_context = false;

    // Erstelle eine neue Kamera für view::camera.
    // Msaa::Off, da Bevy die 2D-Tiefentextur pro Fenster teilt
    // und alle 2D-Kameras (inkl. egui) daher dieselbe Sample-Anzahl haben müssen.
    commands.spawn((
        Camera2d, 
        Camera { order: 0, ..default() }, 
        Msaa::Off, 
        CameraForViewCamera
    ));

    // Erstelle eine neue Kamera für view::sensor2d.
    // Eigener RenderLayer, damit sie weder das Kamerabild noch die YOLO-Gizmos (Layer 0) rendert.
    // AutoMin sorgt dafür, dass das Raster unabhängig von der Viewport-Größe komplett sichtbar ist.
    commands.spawn((
        Camera2d,
        Camera { order: 1, clear_color: ClearColorConfig::Custom(Color::srgb_u8(27, 27, 27)), ..default() },
        Projection::Orthographic(OrthographicProjection {
            scaling_mode: ScalingMode::AutoMin {
                min_width: sensor2d::GRID_SIZE, 
                min_height: sensor2d::GRID_SIZE 
            },
            ..OrthographicProjection::default_2d()
        }),
        Msaa::Off,
        RenderLayers::layer(sensor2d::SENSOR_LAYER),
        CameraForViewSensor,
    ));

    // Erstelle eine neue Kamera für egui.
    // Wird über das ganze Fenster zuletzt gerendert.
    commands.spawn((
        Camera2d,
        Camera {
            order: 2,
            clear_color: ClearColorConfig::Custom(Color::NONE),
            output_mode: CameraOutputMode::Write {
                blend_state: Some(BlendState::PREMULTIPLIED_ALPHA_BLENDING),
                clear_color: ClearColorConfig::None,
            },
            ..default()
        },
        Hdr,
        Msaa::Off,
        PrimaryEguiContext,
        RenderLayers::none(),
    ));
}

/// UI-Layout Aufbau des Analyzers
///
/// Die einzelnen Bereiche, in welchen Bevy rendern muss,
/// werden in `ViewRects` gespeichert und schließlich von `update_viewports`
/// zu Bevy Viewports übersetzt.
fn ui_layout(
    mut contexts: EguiContexts,
    mut rects: ResMut<ViewRects>,
) -> Result {
    let ctx = contexts.ctx_mut()?;

    // Root-UI erzeugen
    let mut root_ui = egui::Ui::new(
        ctx.clone(),
        "root_ui".into(),
        egui::UiBuilder::new()
            .layer_id(egui::LayerId::background())
            .max_rect(ctx.viewport_rect()),
    );

    egui::Window::new("Steuerung")
        .resizable(true)
        .frame(egui::Frame::window(root_ui.style()))
        .show(&mut root_ui, |ui| {

            let rect = ui.available_rect_before_wrap();
            ui.allocate_rect(rect, egui::Sense::hover());
        });


    // Teile die Fläche in zwei Teile
    let half_width = root_ui.available_width() * 0.5;
    egui::Panel::right("eyecam_sensor")
        .resizable(true)
        .default_size(half_width)
        .frame(egui::Frame::NONE)
        .show(&mut root_ui, |ui| {
            // Nehme den Inhalt der rechten Seite,
            // und erstelle daraus ein Rect für den Sensor.
            let rect = ui.available_rect_before_wrap();
            ui.allocate_rect(rect, egui::Sense::hover());
            rects.view_sensor = rect;
        });


    // Nehme den Inhalt der verbleibenden linken Seite,
    // und erstelle daraus ein Rect.
    rects.view_camera = root_ui.available_rect_before_wrap();

    Ok(())
}

/// Rechne die egui-Rects in Viewports um.  
fn update_viewports(
    mut contexts: EguiContexts,
    rects: Res<ViewRects>,
    window: Single<&Window>,
    mut view_camera: Single<&mut Camera, (With<CameraForViewCamera>, Without<CameraForViewSensor>)>,
    mut view_sensor: Single<&mut Camera, (With<CameraForViewSensor>, Without<CameraForViewCamera>)>
) -> Result {
    let ppp = contexts.ctx_mut()?.pixels_per_point();
    let window_size = window.physical_size();

    view_camera.viewport = to_viewport(rects.view_camera, ppp, window_size);
    view_sensor.viewport = to_viewport(rects.view_sensor, ppp, window_size);
    Ok(())
}

/// egui-Rechteck (logische Punkte) -> Bevy-Viewport (physische Pixel), ans Fenster geklemmt.
fn to_viewport(rect: egui::Rect, ppp: f32, window_size: UVec2) -> Option<Viewport> {
    let pos = UVec2::new((rect.min.x * ppp) as u32, (rect.min.y * ppp) as u32).min(window_size);
    let size = UVec2::new((rect.width() * ppp) as u32, (rect.height() * ppp) as u32)
        .min(window_size - pos);

    (size.x > 0 && size.y > 0).then(|| Viewport {
        physical_position: pos,
        physical_size: size,
        ..default()
    })
}
