use crate::reader::{packets::Packet, spawn_eyecam_reader};
use egui_plot::PlotPoints;
use std::collections::VecDeque;
use std::sync::mpsc;
use std::sync::mpsc::Receiver;
use std::time::Instant;
use crate::reader::packets::packet::Payload;
use crate::reader::packets::{GraphLabel, GraphPacket, YoloPacket};

pub struct AnalyzerViewModel {
    rx: Receiver<Packet>,
    zone_left: VecDeque<f32>,
    zone_middle: VecDeque<f32>,
    zone_right: VecDeque<f32>,
    pub(crate) max_points: usize,
    pub start_time: Instant
}

trait AddGraphValue {
    fn add_graph_value(&mut self, value: f32, max_len: usize);
}

impl AddGraphValue for VecDeque<f32> {

    fn add_graph_value(&mut self, value: f32, max_len: usize) {
        self.push_back(value);
        if self.len() > max_len {
            self.pop_front();
        }
    }

}


impl AnalyzerViewModel {
    
    pub fn new() -> AnalyzerViewModel {
        // Start listening
        let (tx, rx) = mpsc::channel::<Packet>();
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

    fn receive_yolo_packet(&self, packet: YoloPacket) {

    }

    fn receive_graph_packet(&mut self, packet: GraphPacket) {
        // Apply for zone middle
        for graph in packet.graphs {
            let label = GraphLabel::try_from(graph.name).unwrap();

            match label {
                GraphLabel::ZoneLeft =>
                    self.zone_left.add_graph_value(graph.value, self.max_points),
                GraphLabel::ZoneMiddle =>
                    self.zone_middle.add_graph_value(graph.value, self.max_points),
                GraphLabel::ZoneRight =>
                    self.zone_right.add_graph_value(graph.value, self.max_points),
            }
        }

    }

    pub fn fetch_data(&mut self) -> Vec<PlotPoints> {
        while let Ok(packet) = self.rx.try_recv() {

            match packet.payload {
                None => { println!("Received empty packet.") }
                Some(payload) => {
                    match payload {
                        Payload::Yolo(yolo) => self.receive_yolo_packet(yolo),
                        Payload::Graph(graph) => self.receive_graph_packet(graph)
                    }
                }
            }

        }

        //TODO: In extra Funktion auslagern / Aufruf überdenken
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