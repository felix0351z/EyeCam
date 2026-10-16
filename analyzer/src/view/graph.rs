use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiPrimaryContextPass};
use egui::Color32;
use egui_plot::{HLine, Legend, Line, LineStyle, Plot, PlotPoints};
use std::collections::VecDeque;
use crate::receiver::{GraphHistory, GRAPH_HISTORY_SECS};
use crate::view::UiState;

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct GraphViewPlugin;
impl Plugin for GraphViewPlugin {
    fn build(&self, app: &mut App) {
        app.add_systems(EguiPrimaryContextPass, show_graph_window);
    }
}

/// Schwelle, ab welcher die ZoneDetection ausweicht.
/// Muss mit `ZoneDetection.MOVE_THRESHOLD` in der App übereinstimmen.
const MOVE_THRESHOLD: f64 = 0.5;

/// Name und Farbe der Zonen, Index entspricht `protocol::Zone`.
const ZONES: [(&str, Color32); 3] = [
    ("Links", Color32::from_rgb(66, 135, 245)),
    ("Mitte", Color32::from_rgb(245, 166, 35)),
    ("Rechts", Color32::from_rgb(80, 200, 120)),
];

// --------------------------------------
// Systeme und Hilfsfunktionen
// --------------------------------------

/// Zeige das Fenster mit dem Verlauf der Gefahrenwerte,
/// solange es in der Steuerung aktiviert ist.
///
/// Pro Zone eine Farbe: YOLO durchgezogen, Sensor gestrichelt.
fn show_graph_window(
    mut contexts: EguiContexts,
    mut ui_state: ResMut<UiState>,
    history: Res<GraphHistory>,
    time: Res<Time>,
) -> Result {
    let ctx = contexts.ctx_mut()?;
    let now = time.elapsed_secs_f64();

    // Über das Schließen-Kreuz wird auch die Checkbox in der Steuerung zurückgesetzt.
    egui::Window::new("Gefahrenwerte")
        .open(&mut ui_state.show_graph)
        .default_size([1200.0, 600.0])
        .show(ctx, |ui| {
            Plot::new("danger_plot")
                .legend(Legend::default())
                .x_axis_label("Zeit [s]")
                .y_axis_label("Gefahr")
                .allow_drag(false)
                .allow_zoom(false)
                .allow_scroll(false)
                .show(ui, |plot_ui| {
                    // Feste Achsen: Die letzten Sekunden laufen von rechts nach links durch.
                    plot_ui.set_plot_bounds_x(now - GRAPH_HISTORY_SECS..=now);
                    plot_ui.set_plot_bounds_y(-0.05..=1.05);

                    plot_ui.hline(
                        HLine::new("Schwelle", MOVE_THRESHOLD)
                            .color(Color32::GRAY)
                            .style(LineStyle::dashed_dense())
                    );

                    for (zone, (name, color)) in ZONES.iter().enumerate() {
                        plot_ui.line(
                            Line::new(format!("YOLO {name}"), to_points(&history.yolo[zone]))
                                .color(*color)
                        );
                        plot_ui.line(
                            Line::new(format!("Sensor {name}"), to_points(&history.sensor[zone]))
                                .color(*color)
                                .style(LineStyle::dashed_loose())
                        );
                    }
                });
        });

    Ok(())
}

fn to_points(points: &VecDeque<[f64; 2]>) -> PlotPoints<'static> {
    points.iter().copied().collect()
}
