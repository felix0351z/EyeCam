use bevy::prelude::*;
use bevy_egui::EguiContexts;
use egui::Ui;

#[derive(Resource)]
pub struct ViewRects {
    view2d: egui::Rect,
    view3d: egui::Rect
}

impl Default for ViewRects {
    fn default() -> Self {
        ViewRects {
            view2d: egui::Rect::ZERO,
            view3d: egui::Rect::ZERO,
        }
    }
}

#[derive(Component)]
pub struct View2dCamera;

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


pub fn ui_layout(
    mut contexts: EguiContexts,
    mut rects: ResMut<ViewRects>,
    plot: Res<PlotData>,
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

    let half_width = root_ui.available_width() * 0.5;

    // Rechte Seite ohne eigenen Hintergrund, damit die 3D-Ansicht durchscheint.
    egui::Panel::right("rechts")
        .resizable(true)
        .default_size(half_width)
        .frame(egui::Frame::NONE) // ältere egui: egui::Frame::none()
        .show(&mut root_ui, |ui| {
            egui::Panel::top("plot")
                .resizable(true)
                .default_size(ui.available_height() * 0.5)
                .show(ui, |ui| plot_view(ui, &plot));

            // Was im rechten Panel übrig bleibt, gehört der 3D-Ansicht.
            rects.view3d = ui.available_rect_before_wrap();
        });

    // Kein CentralPanel: der Rest des Fensters gehört der 2D-Ansicht.
    rects.view2d = root_ui.available_rect_before_wrap();
    Ok(())
}

fn plot_view(ui: &mut Ui, data: &PlotData) {

    let points: egui_plot::PlotPoints = data.values.iter().copied().collect();

    egui_plot::Plot::new("messwerte").show(ui, |plot_ui| {
        plot_ui.line(egui_plot::Line::new("Messwerte", points));
    });
}




