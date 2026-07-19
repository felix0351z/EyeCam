use std::time::{Duration};
use eframe::{App, Frame};
use egui::Ui;
use egui_plot::{Line, Plot, PlotPoints, PlotResponse};
use crate::viewmodel::AnalyzerViewModel;

pub struct AnalyzerView {
    vm: AnalyzerViewModel
}

/// Create the view
/// This is the entrypoint for the app in main.rs
impl Default for AnalyzerView {

    fn default() -> Self {
        Self { vm: AnalyzerViewModel::new() }
    }

}


/// UI Top Root
impl App for AnalyzerView {
    fn ui(&mut self, ui: &mut Ui, _frame: &mut Frame) {
        egui::CentralPanel::default().show(ui, |ui| {
            self.show_plot(ui)
        });
    }
}

/// All UI Panels
impl AnalyzerView {


    fn show_plot(&mut self, ui: &mut Ui) {
        let max = self.vm.max_points;
        let points = self.vm.fetch_data();

        egui::CentralPanel::default().show(ui, |ui| {
            let available_height = ui.available_height();
            let plot_height = available_height / 3.0;


            // Left
            ui.heading("Zone Left");
            Self::new_plot("left", max)
                .height(plot_height)
                .show(ui, |plot_ui| {
                    plot_ui.line(Line::new("a", points[0].points()))
                });


            // Middle
            ui.heading("Zone Middle");
            Self::new_plot("middle", max)
                .height(plot_height)
                .show(ui, |plot_ui| {
                    plot_ui.line(Line::new("b", points[1].points()))
                });


            //Right
            ui.heading("Zone Right");
            Self::new_plot("right", max)
                .height(plot_height)
                .show(ui, |plot_ui| {
                    plot_ui.line(Line::new("c", points[2].points()))
                });

        });

        ui.request_repaint_after(Duration::from_millis(50));
    }

pub fn new_plot<'a>(id_source: impl egui::AsId, n_x: usize) -> Plot<'a> {
    Plot::new(id_source)
        //.view_aspect(2.0)
        .include_y(1.0)
        .include_y(0.0)
        .include_x(0.0)
        .include_x(n_x as f64)
}








}