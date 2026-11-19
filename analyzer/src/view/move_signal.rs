use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiPrimaryContextPass};
use egui::{Align2, Color32, RichText};
use crate::backend::protocol::MoveDirection;
use crate::receiver::MoveSignals;
use super::ViewRects;

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct MoveSignalViewPlugin;
impl Plugin for MoveSignalViewPlugin {
    fn build(&self, app: &mut App) {
        // Nach dem Layout, damit das Rect der Kameraansicht aktuell ist.
        app.add_systems(EguiPrimaryContextPass, show_move_signal.after(super::ui_layout));
    }
}

/// Anzeigedauer eines Signals.
/// Entspricht dem Cooldown in `DetectionAlgorithm._move()`, früher kommt kein neues Signal.
const DISPLAY_SECS: f64 = 2.0;
/// Am Ende der Anzeigedauer wird das Banner über diese Zeit ausgeblendet.
const FADE_SECS: f64 = 0.5;
const BANNER_MARGIN_TOP: f32 = 16.0;
const BANNER_TEXT_SIZE: f32 = 36.0;

/// Text und Farbe eines Ausweichsignals.
/// Wird auch für die Markierungen im Plot (`view::graph`) verwendet.
pub fn signal_style(direction: MoveDirection) -> (&'static str, Color32) {
    match direction {
        MoveDirection::Left => ("⬅ LINKS", Color32::from_rgb(230, 160, 30)),
        MoveDirection::Right => ("RECHTS ➡", Color32::from_rgb(160, 100, 230)),
        MoveDirection::Stop => ("✋ STOPP", Color32::from_rgb(210, 50, 50)),
    }
}

// --------------------------------------
// Systeme
// --------------------------------------

/// Zeige das neueste Ausweichsignal als Banner oben mittig über dem Kamerabild.
fn show_move_signal(
    mut contexts: EguiContexts,
    signals: Res<MoveSignals>,
    rects: Res<ViewRects>,
    time: Res<Time>,
) -> Result {
    let Some(&(received_at, direction)) = signals.0.back() else { return Ok(()) };

    let age = time.elapsed_secs_f64() - received_at;
    if age > DISPLAY_SECS {
        return Ok(());
    }

    // Volle Deckkraft, erst in den letzten FADE_SECS ausblenden.
    let alpha = ((DISPLAY_SECS - age) / FADE_SECS).clamp(0.0, 1.0) as f32;
    let (text, color) = signal_style(direction);

    let ctx = contexts.ctx_mut()?;
    egui::Area::new(egui::Id::new("move_signal"))
        .order(egui::Order::Foreground)
        .interactable(false)
        .pivot(Align2::CENTER_TOP)
        .fixed_pos(rects.view_camera.center_top() + egui::vec2(0.0, BANNER_MARGIN_TOP))
        .show(ctx, |ui| {
            egui::Frame::new()
                .fill(color.gamma_multiply(alpha))
                .corner_radius(8)
                .inner_margin(egui::Margin::symmetric(24, 12))
                .show(ui, |ui| {
                    ui.label(
                        RichText::new(text)
                            .size(BANNER_TEXT_SIZE)
                            .strong()
                            .color(Color32::WHITE.gamma_multiply(alpha))
                    );
                });
        });

    Ok(())
}
