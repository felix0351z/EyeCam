mod view;
mod viewmodel;
mod reader;

pub const APP_NAME: &'static str = "EyeCam Analyzer";

fn main() {
    env_logger::init();

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1920.0, 1080.0]),
        ..Default::default()
    };

    eframe::run_native(APP_NAME, options, Box::new(|creation_context| {
        creation_context.egui_ctx.set_theme(egui::Theme::Dark);
        Ok(Box::<view::AnalyzerView>::default())
    })).expect("Failed to run app");


}
