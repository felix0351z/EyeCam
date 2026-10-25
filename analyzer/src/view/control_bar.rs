use bevy::ecs::system::SystemParam;
use bevy::prelude::*;
use crate::receiver::{EyeCamConnection, EyeCamStatus};
use crate::view::UiState;

const STATUS_DOT_SIZE: f32 = 10.0;
const COLOR_CONNECTED: egui::Color32 = egui::Color32::from_rgb(60, 200, 90);
const COLOR_DISCONNECTED: egui::Color32 = egui::Color32::from_rgb(220, 60, 60);

/// Ressourcen, welche die Steuerleiste zum Anzeigen und Senden von Befehlen benötigt.
#[derive(SystemParam)]
pub struct ControlBarParams<'w> {
    ui_state: ResMut<'w, UiState>,
    status: Res<'w, EyeCamStatus>,
    connection: Res<'w, EyeCamConnection>,
    time: Res<'w, Time>,
}

/// Zeige die Steuerleiste am unteren Fensterrand.
///
/// Muss vor den übrigen Panels aufgerufen werden,
/// damit die Leiste über die volle Fensterbreite geht.
pub fn show(root_ui: &mut egui::Ui, params: &mut ControlBarParams) {
    egui::Panel::bottom("control_bar")
        .frame(egui::Frame::side_top_panel(root_ui.style()))
        .show(root_ui, |ui| {
            ui.horizontal(|ui| {
                // Zustand und Auswahl richten sich nach dem von der EyeCam gemeldeten Status,
                // nicht nach dem zuletzt gesendeten Befehl.
                let connected = params.status.connected(params.time.elapsed_secs_f64());

                show_connection_state(ui, connected, params.status.running);

                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    show_run_selector(ui, connected, params);
                    ui.separator();
                    ui.checkbox(&mut params.ui_state.show_graph, "Gefahrenwerte anzeigen");
                });
            });
        });
}

/// Farbiger Punkt und Text für den Verbindungsstatus.
fn show_connection_state(ui: &mut egui::Ui, connected: bool, running: bool) {
    let (rect, _) = ui.allocate_exact_size(egui::Vec2::splat(STATUS_DOT_SIZE), egui::Sense::hover());
    let color = if connected { COLOR_CONNECTED } else { COLOR_DISCONNECTED };
    ui.painter().circle_filled(rect.center(), STATUS_DOT_SIZE * 0.5, color);

    let state = match (connected, running) {
        (false, _) => "Nicht verbunden",
        (true, true) => "Läuft",
        (true, false) => "Pausiert",
    };
    ui.label(format!("EyeCam: {state}"));
}

/// Auswahl zwischen Start und Pause, sendet bei Änderung einen Befehl an die EyeCam.
fn show_run_selector(ui: &mut egui::Ui, connected: bool, params: &ControlBarParams) {
    let mut running = params.status.running;

    ui.add_enabled_ui(connected, |ui| {
        egui::ComboBox::from_id_salt("run_state")
            .selected_text(if running { "Start" } else { "Pause" })
            .show_ui(ui, |ui| {
                ui.selectable_value(&mut running, true, "Start");
                ui.selectable_value(&mut running, false, "Pause");
            });
    });

    if running != params.status.running {
        params.connection.0.set_running(running);
    }
}
