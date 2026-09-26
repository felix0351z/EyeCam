pub mod camera;

use bevy::camera::Viewport;
use bevy::prelude::*;
use bevy_egui::EguiContexts;
use crossbeam_channel::Receiver;
use crate::backend::protocol;

/// Crossbeam-Receiver, von welchem neue Message-Pakete kommen
#[derive(Resource)]
pub struct MessageReceiver(pub Receiver<protocol::Message>);

/// Neueste, noch nicht verarbeitete Yolo-Nachricht.
/// Wird von `receive_messages` befüllt und vom Konsumenten per `take()` geleert.
#[derive(Resource, Default)]
pub struct LatestYoloMessage(pub Option<protocol::YoloMessage>);

/// Leert den Channel komplett und merkt sich pro Nachrichtentyp nur die neueste Nachricht.
pub fn receive_messages(
    receiver: Res<MessageReceiver>,
    mut latest_yolo: ResMut<LatestYoloMessage>,
) {
    for message in receiver.0.try_iter() {
        match message {
            protocol::Message::Yolo(yolo) => latest_yolo.0 = Some(yolo),
            protocol::Message::Graph(_) => {}
        }
    }
}


/// Ressource, welche die Rects für die Bevy-Views beinhaltet.
/// Bevy nutzt diese egui-Rects und zeichnet seinen Inhalt hinein.
#[derive(Resource)]
pub struct ViewRects {
    pub view_camera: egui::Rect,
    //pub view_sensor: egui::Rect
}

impl Default for ViewRects {
    fn default() -> Self {
        ViewRects {
            view_camera: egui::Rect::ZERO,
            //view_sensor: egui::Rect::ZERO,
        }
    }
}

/// Bevy-Kameraobjekt, welches auf das passende Viewport im Fenster zeigt.
#[derive(Component)]
pub struct CameraForViewCamera;


pub fn ui_layout(
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
    egui::Panel::right("eyecam_camera")
        .resizable(true)
        .default_size(half_width)
        .frame(egui::Frame::NONE)
        .show(&mut root_ui, |ui| {
            
            let rect = ui.available_rect_before_wrap();
            ui.allocate_rect(rect, egui::Sense::hover());
        });

    // Nehme den Inhalt der verbleibenden linken Seite,
    // und erstelle daraus ein Rect.

    rects.view_camera = root_ui.available_rect_before_wrap();
    // rects.view3d = root_ui.available_rect_before_wrap();


    Ok(())
}

/// Rechne die egui-Rects in Viewports um.  
pub fn update_viewports(
    mut contexts: EguiContexts,
    rects: Res<ViewRects>,
    window: Single<&Window>,
    mut view_camera: Single<&mut Camera, With<CameraForViewCamera>>,
) -> Result {
    let ppp = contexts.ctx_mut()?.pixels_per_point();
    let window_size = window.physical_size();

    view_camera.viewport = to_viewport(rects.view_camera, ppp, window_size);
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
