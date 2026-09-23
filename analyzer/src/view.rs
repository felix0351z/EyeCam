use bevy::camera::Viewport;
use bevy::prelude::*;
use bevy_egui::EguiContexts;
use crossbeam_channel::Receiver;
use crate::backend::protocol;

/// Ressource, welche die Rects für die Bevy-Views beinhaltet.
/// Bevy nutzt diese egui-Rects und zeichnet seinen Inhalt hinein.
#[derive(Resource)]
pub struct ViewRects {
    pub view_camera: egui::Rect,
    //pub view3d: egui::Rect
}

impl Default for ViewRects {
    fn default() -> Self {
        ViewRects {
            view_camera: egui::Rect::ZERO,
            //view3d: egui::Rect::ZERO,
        }
    }
}

#[derive(Resource)]
pub struct CameraReceiver(pub Receiver<protocol::Message>);


#[derive(Component)]
pub struct ViewEyecamCamera;



/*
#[derive(Component)]
pub struct View3dCamera;

#[derive(Resource)]
pub struct PlotData {
    values: Vec<[f64; 2]>,
}

impl Default for PlotData {
    fn default() -> Self {
        let values = (0..200).map(|i| {
            let x = i as f64 * 0.05;
            [x, x.sin()]
        });
        Self { values: values.collect() }
    }
}
*/

pub fn ui_layout(
    mut contexts: EguiContexts,
    mut rects: ResMut<ViewRects>,
    //plot: Res<PlotData>,
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

            //rects.view3d = ui.available_rect_before_wrap();
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


    rects.view_camera = root_ui.available_rect_before_wrap();
    // rects.view3d = root_ui.available_rect_before_wrap();


    Ok(())
}

/*
fn plot_view(ui: &mut Ui, data: &PlotData) {

    let points: egui_plot::PlotPoints = data.values.iter().copied().collect();

    egui_plot::Plot::new("messwerte").show(ui, |plot_ui| {
        plot_ui.line(egui_plot::Line::new("Messwerte", points));
    });
}*/


pub fn update_viewports(
    mut contexts: EguiContexts,
    rects: Res<ViewRects>,
    window: Single<&Window>,
    mut cam2d: Single<&mut Camera, With<ViewEyecamCamera>>,
    //mut cam3d: Single<&mut Camera, (With<View3dCamera>, Without<View2dCamera>)>,
) -> Result {
    let ppp = contexts.ctx_mut()?.pixels_per_point();
    let window_size = window.physical_size();

    cam2d.viewport = to_viewport(rects.view_camera, ppp, window_size);
    //cam3d.viewport = to_viewport(rects.view3d, ppp, window_size);
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




