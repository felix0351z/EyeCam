use std::collections::VecDeque;
use bevy::prelude::*;
use crossbeam_channel::Receiver;
use crate::backend::protocol;
use crate::backend;

/// Zeitraum in Sekunden, welcher in der `GraphHistory` gespeichert wird.
pub const GRAPH_HISTORY_SECS: f64 = 10.0;

/// Ohne Status-Paket (Heartbeat) innerhalb dieser Zeit gilt die EyeCam als nicht verbunden.
const STATUS_TIMEOUT_SECS: f64 = 2.0;

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct ReceiverPlugin;
impl Plugin for ReceiverPlugin {
    fn build(&self, app: &mut App) {
        app
            .init_resource::<LatestYoloMessage>()
            .init_resource::<LatestSensorMessage>()
            .init_resource::<GraphHistory>()
            .init_resource::<EyeCamStatus>()
            .init_resource::<EyeCamConnection>()
            .add_systems(Startup, setup)
            .add_systems(Update, receive_messages.in_set(ReceiveSet));
    }
}

/// SystemSet für alle Systeme, welche neue Daten vom EyeCam-Receiver holen.
/// Systeme, die diese Daten verarbeiten, sollten mit `.after(ReceiveSet)` laufen.
#[derive(SystemSet, Debug, Clone, PartialEq, Eq, Hash)]
pub struct ReceiveSet;


// --------------------------------------
// Ressourcen
// --------------------------------------

/// Halter des Crossbeam-Receivers,
/// von welchem die neuen Message-Pakete kommen
#[derive(Resource)]
struct MessageReceiver(Receiver<protocol::Message>);

/// Neueste, noch nicht verarbeitete Yolo-Nachricht.
/// Wird von `receive_messages` befüllt und vom Konsumenten per `take()` geleert.
#[derive(Resource, Default)]
pub struct LatestYoloMessage(pub Option<protocol::YoloMessage>);

/// Neuste, noch nicht verarbeitete Sensor-Nachricht.
/// Wird von `receive_messages` befüllt und vom Konsumenten per `take()` geleert.
#[derive(Resource, Default)]
pub struct LatestSensorMessage(pub Option<protocol::SensorMessage>);

/// Verlauf der Gefahrenwerte der ZoneDetection der letzten `GRAPH_HISTORY_SECS` Sekunden.
///
/// Anders als bei Yolo und Sensor wird hier nicht nur die neueste Nachricht gehalten,
/// da der Plot den zeitlichen Verlauf benötigt.
/// Ein Punkt ist `[Empfangszeit in s seit App-Start, Wert]`, der Array-Index ist die `Zone`.
#[derive(Resource, Default)]
pub struct GraphHistory {
    pub yolo: [VecDeque<[f64; 2]>; 3],
    pub sensor: [VecDeque<[f64; 2]>; 3],
}

impl GraphHistory {
    /// Füge einen neuen Wert hinzu und verwerfe Werte, die älter als `GRAPH_HISTORY_SECS` sind.
    fn push(&mut self, time: f64, graph: protocol::GraphValue) {
        let series = match graph.source {
            protocol::GraphSource::Yolo => &mut self.yolo,
            protocol::GraphSource::Sensor => &mut self.sensor,
        };
        let points = &mut series[graph.zone as usize];

        points.push_back([time, graph.value as f64]);
        while points.front().is_some_and(|point| time - point[0] > GRAPH_HISTORY_SECS) {
            points.pop_front();
        }
    }
}


/// Zuletzt von der EyeCam gemeldeter Zustand.
#[derive(Resource, Default)]
pub struct EyeCamStatus {
    pub running: bool,
    /// Empfangszeit des letzten Status-Pakets (s seit App-Start).
    last_update: Option<f64>,
}

impl EyeCamStatus {
    /// Verbunden, solange Status-Pakete (Heartbeats) ankommen.
    pub fn connected(&self, now: f64) -> bool {
        self.last_update.is_some_and(|time| now - time < STATUS_TIMEOUT_SECS)
    }
}

/// Verbindung zum Senden von Befehlen an die EyeCam.
#[derive(Resource, Default)]
pub struct EyeCamConnection(pub backend::EyeCamControl);


// --------------------------------------
// Systeme und Hilfsfunktionen
// --------------------------------------

/// Starte den TCP-Client in einem neuen Background-Thread.
///
/// Die Kommunikation funktioniert mit einem Crossbeam-Channel,
/// wobei der Receiver im `MessageReceiver` gespeichert wird und von
/// `receive_messages` ausgelesen wird.
/// Der Thread erhält außerdem eine Kopie von `EyeCamConnection`,
/// um die aktuelle Verbindung für Befehle bereitzustellen.
fn setup(mut commands: Commands, connection: Res<EyeCamConnection>) {
    let (tx, rx) = crossbeam_channel::bounded(2);
    commands.insert_resource(MessageReceiver(rx));

    backend::spawn_eyecam_receiver(tx, connection.0.clone());
}


/// Lese den Crossbeam-Channel aus.
/// Speichere immer die letzte Nachricht vom jeweiligen Typ,
/// Graph-Werte werden an die `GraphHistory` angehängt.
fn receive_messages(
    receiver: Res<MessageReceiver>,
    time: Res<Time>,
    mut yolo_message: ResMut<LatestYoloMessage>,
    mut sensor_message: ResMut<LatestSensorMessage>,
    mut graph_history: ResMut<GraphHistory>,
    mut eyecam_status: ResMut<EyeCamStatus>,
) {
    let now = time.elapsed_secs_f64();

    for message in receiver.0.try_iter() {
        match message {
            protocol::Message::Yolo(yolo) => yolo_message.0 = Some(yolo),
            protocol::Message::Sensor(sensor) => sensor_message.0 = Some(sensor),
            protocol::Message::Graph(graph) => {
                for value in graph.graphs {
                    graph_history.push(now, value);
                }
            }
            protocol::Message::Status(status) => {
                eyecam_status.running = status.running;
                eyecam_status.last_update = Some(now);
            }
        }
    }
}