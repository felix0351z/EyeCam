use crate::reader::{spawn_eyecam_reader, EyeCamData, GraphLabel};
use std::collections::VecDeque;
use std::sync::mpsc;
use std::sync::mpsc::Receiver;
use std::time::Instant;
use egui::IntoAtoms;
use egui_plot::{PlotPoint, PlotPoints};

pub struct AnalyzerViewModel {
    rx: Receiver<EyeCamData>,
    zone_left: VecDeque<f32>,
    zone_middle: VecDeque<f32>,
    zone_right: VecDeque<f32>,
    pub(crate) max_points: usize,
    pub start_time: Instant
}


impl AnalyzerViewModel {
    
    pub fn new() -> AnalyzerViewModel {
        // Start listening
        let (tx, rx) = mpsc::channel::<EyeCamData>();
        let n_points = 2000;

        spawn_eyecam_reader(tx);
        AnalyzerViewModel { rx,
            zone_left: VecDeque::with_capacity(n_points),
            zone_middle: VecDeque::with_capacity(n_points),
            zone_right: VecDeque::with_capacity(n_points),
            max_points: n_points,
            start_time: Instant::now()
        }
    }

    pub fn fetch_data(&mut self) -> Vec<PlotPoints> {
        while let Ok(data) = self.rx.try_recv() {

            // Apply for zone middle
            for graph in data.graphs {
                match graph.label {
                    GraphLabel::ZoneLeft => {
                        self.zone_left.push_back(graph.value);
                        if self.zone_left.len() > self.max_points {
                            self.zone_left.pop_front();
                        }
                    }
                    GraphLabel::ZoneMiddle => {
                        self.zone_middle.push_back(graph.value);
                        if self.zone_middle.len() > self.max_points {
                            self.zone_middle.pop_front();
                        }
                    }
                    GraphLabel::ZoneRight => {
                        self.zone_right.push_back(graph.value);
                        if self.zone_right.len() > self.max_points {
                            self.zone_right.pop_front();
                        }
                    }
                }
            }
        }

        let graphs = [&self.zone_left, &self.zone_middle, &self.zone_right];
        let points: Vec<PlotPoints> = graphs
            .iter()
            .map(|graph| {
                let x: PlotPoints = graph
                    .iter().enumerate()
                    .map(|(i, v)| [i as f64, *v as f64])
                    .collect();
                x
            })
            .collect();

        points
    }


    
    
}