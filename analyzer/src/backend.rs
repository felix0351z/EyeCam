use crate::backend::protocol::{GraphMessage, GraphSource, GraphValue, MoveDirection, SensorMessage, StatusMessage, YoloMessage, Zone};
use crate::logger::PacketLogger;
use crossbeam_channel::Sender;
use prost::Message;
use std::io::{BufReader, Read, Write};
use std::net::TcpStream;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use zune_jpeg::JpegDecoder;
use zune_jpeg::zune_core::bytestream::ZCursor;
// --------------------------------------
// Einstiegspunkt
// --------------------------------------
const EYECAM_ADDRESS: &str = "eyecam.local:6969";
const RETRY_INTERVAL: Duration = Duration::from_secs(2);
const READ_TIMEOUT: Duration = Duration::from_secs(2);
/// Befehle werden aus dem UI-Thread gesendet, dieser darf nicht lange blockieren.
const WRITE_TIMEOUT: Duration = Duration::from_millis(100);

/// Spawne einen neuen Thread um Daten vom EyeCam-Gerät zu empfangen.
///
/// Während eine Verbindung besteht, wird ein zweites Handle auf den Socket
/// in `control` hinterlegt, über welches die UI Befehle senden kann.
pub fn spawn_eyecam_receiver(tx: Sender<protocol::Message>, control: EyeCamControl) {
    std::thread::spawn(move || {
        let mut logger = PacketLogger::new()
            .inspect_err(|e| eprintln!("Packet-Logger deaktiviert: {e}"))
            .ok();

        loop {
            let Ok(stream) = TcpStream::connect(EYECAM_ADDRESS) else {
                std::thread::sleep(RETRY_INTERVAL);
                continue;
            };
            stream.set_read_timeout(Some(READ_TIMEOUT)).ok();
            stream.set_write_timeout(Some(WRITE_TIMEOUT)).ok();
            control.set_stream(stream.try_clone().ok());

            if let Ok(peer_ip) = stream.peer_addr() {
                println!("Connected to EyeCam device on ip {}", peer_ip);
            }

            let mut buf_reader = BufReader::new(&stream);
            while let Ok(frame) = read_frame(&mut buf_reader) {
                if let Some(l) = logger.as_mut() {
                    if let Err(e) = l.log(&frame) {
                        eprintln!("Logging fehlgeschlagen, Logger deaktiviert: {e}");
                        logger = None;
                    }
                }

                // Kaputte Pakete überspringen, das Framing bleibt dabei intakt.
                let Ok(packet) = api::Packet::decode(&frame[..]) else { continue };

                // Send a new message through the channel if a payload is available.
                if let Ok(msg) = packet.try_into() {
                    if tx.send(msg).is_err() {
                        return;
                    }
                }
            }

            if let Some(l) = logger.as_mut() {
                let _ = l.flush();
            }
            control.set_stream(None);
            eprintln!("Connection closed. Reconnecting...");
        }
    });
}

/// Schreibender Zugriff auf die aktuelle Verbindung zur EyeCam.
///
/// Der Empfangs-Thread setzt beim Verbinden ein zweites Handle auf den Socket
/// und entfernt es beim Trennen. Die UI sendet darüber Befehle.
#[derive(Clone, Default)]
pub struct EyeCamControl(Arc<Mutex<Option<TcpStream>>>);

impl EyeCamControl {
    /// Starte oder pausiere die Verarbeitung auf der EyeCam.
    pub fn set_running(&self, running: bool) {
        self.send(api::Command {
            payload: Some(api::command::Payload::Running(running)),
        });
    }

    /// Sende einen Befehl mit 4 Byte Längenpräfix (Big Endian).
    /// Fehler werden ignoriert, ein Verbindungsabbruch wird vom Empfangs-Thread erkannt.
    fn send(&self, command: api::Command) {
        let payload = command.encode_to_vec();
        let mut frame = (payload.len() as u32).to_be_bytes().to_vec();
        frame.extend_from_slice(&payload);

        if let Some(stream) = self.0.lock().unwrap().as_mut() {
            let _ = stream.write_all(&frame);
        }
    }

    fn set_stream(&self, stream: Option<TcpStream>) {
        *self.0.lock().unwrap() = stream;
    }
}

// --------------------------------------
// Funktionen
// --------------------------------------

/// Lese einen Frame mit 4 Byte Längenpräfix (Big Endian) aus dem Stream.
fn read_frame(reader: &mut impl Read) -> std::io::Result<Vec<u8>> {
    // Länge der Paketgröße.
    // Dieser ist vom Typ u32 und wird daher mit 4 Bytes angegeben.
    let mut len_buf = [0u8; 4];

    // Lese die Paketgröße
    reader.read_exact(&mut len_buf)?;
    let size = u32::from_be_bytes(len_buf) as usize;

    // Paket lesen und in einem Vec-Buffer zwischenspeichern.
    let mut frame = vec![0u8; size];
    reader.read_exact(&mut frame)?;
    Ok(frame)
}


/// Dekodiere ein Jpeg-Bild
fn decode_jpeg(jpeg_bytes: Vec<u8>) -> protocol::Jpeg {
    let cursor = ZCursor::new(jpeg_bytes);
    let mut decoder = JpegDecoder::new(cursor);

    decoder.decode_headers()
        .expect("Failed to decode JPEG headers");

    let (width, height) = decoder.dimensions()
        .expect("No dimensions");

    let rgb = decoder.decode()
        .expect("Failed to decode Jpeg");

    // Wandle in RGBA um, da Bevy kein RGB direkt nimmt.
    let rgba: Vec<u8> = rgb
        .chunks_exact(3)
        .flat_map(|p| [p[0], p[1], p[2], 255])
        .collect();

    protocol::Jpeg {data: rgba, width, height}
}

// --------------------------------------
// Protobuf-API & Channel-Protokoll
// --------------------------------------

/// API zwischen EyeCam und dem Analyzer.
/// Generiert aus der `packets.proto` Datei.
pub mod api {
    include!(concat!(env!("OUT_DIR"), "/packets.rs"));
}


/// Protokoll für die Kommunikation zwischen Backend und Bevy-UI
/// auf dem Crossbeam-Channel
pub mod protocol {

    #[derive(Clone, PartialEq)]
    pub enum Message {
        Yolo(YoloMessage),
        Graph(GraphMessage),
        Sensor(SensorMessage),
        Status(StatusMessage),
        Move(MoveDirection),
    }

    /// Zustand der EyeCam, wird regelmäßig als Heartbeat gesendet.
    #[derive(Copy, Clone, PartialEq)]
    pub struct StatusMessage {
        pub running: bool,
    }

    /// Richtung eines von der Detection ausgelösten Ausweichsignals.
    #[derive(Copy, Clone, PartialEq, Eq, Debug)]
    pub enum MoveDirection {
        Left,
        Right,
        Stop,
    }

    #[derive(Clone, PartialEq)]
    pub struct YoloMessage {
        pub frame_id: u64,
        pub timestamp_ms: u64,
        pub jpeg: Jpeg,
        pub confidences: Vec<f32>,
        pub class_ids: Vec<i32>,
        // 2-D Array [N; 4] für x1, y1, x2, y2
        pub boxes: Vec<f32>
    }

    #[derive(Clone, PartialEq)]
    pub struct SensorMessage {
        pub distance_mm: Vec<i16>, // in mm
        pub range_sigma_mm: Vec<u16>, // in mm
        pub target_status: Vec<u8>, // Statuscode
    }

    #[derive(Clone, PartialEq)]
    pub struct Jpeg {
        pub data: Vec<u8>,
        pub width: usize,
        pub height: usize
    }

    #[derive(Clone, PartialEq)]
    pub struct GraphMessage {
        pub frame_id: u64,
        pub graphs: Vec<GraphValue>
    }

    /// Geglätteter Gefahrenwert (0-1) einer Zone der ZoneDetection.
    #[derive(Copy, Clone, PartialEq)]
    pub struct GraphValue {
        pub source: GraphSource,
        pub zone: Zone,
        pub value: f32,
    }

    /// Quelle, aus welcher der Gefahrenwert berechnet wurde.
    #[derive(Copy, Clone, PartialEq, Eq, Debug)]
    pub enum GraphSource {
        Yolo,
        Sensor,
    }

    /// Zone der ZoneDetection.
    /// Der Wert entspricht dem Index (links nach rechts).
    #[derive(Copy, Clone, PartialEq, Eq, Debug)]
    pub enum Zone {
        Left = 0,
        Middle = 1,
        Right = 2,
    }
}



/// Error-Typ, falls keine Payload mit dem Packet übertragen wird.
#[derive(Debug, Clone)]
pub struct NoPayloadError;

impl std::fmt::Display for NoPayloadError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "Keine Payload im Paket vorhanden!")
    }
}

/// Implementationen der Traits
/// für die Konvertierung zwischen API und dem Channel Protokoll.
impl TryFrom<api::GraphValue> for GraphValue {
    type Error = prost::UnknownEnumValue;
    fn try_from(value: api::GraphValue) -> Result<Self, Self::Error> {
        let (source, zone) = match api::GraphLabel::try_from(value.name)? {
            api::GraphLabel::YoloLeft => (GraphSource::Yolo, Zone::Left),
            api::GraphLabel::YoloMiddle => (GraphSource::Yolo, Zone::Middle),
            api::GraphLabel::YoloRight => (GraphSource::Yolo, Zone::Right),
            api::GraphLabel::SensorLeft => (GraphSource::Sensor, Zone::Left),
            api::GraphLabel::SensorMiddle => (GraphSource::Sensor, Zone::Middle),
            api::GraphLabel::SensorRight => (GraphSource::Sensor, Zone::Right),
        };
        Ok(GraphValue { source, zone, value: value.value })
    }
}
impl From<api::GraphPacket> for GraphMessage {
    fn from(value: api::GraphPacket) -> Self {
        GraphMessage {
            frame_id: value.frame_id,
            // Unbekannte Labels (z.B. neuere Proto-Version auf der EyeCam) werden verworfen.
            graphs: value.graphs.into_iter()
                .filter_map(|graph| GraphValue::try_from(graph).ok())
                .collect(),
        }
    }
}

fn to_f32(b: &[u8]) -> Vec<f32> {
    b.chunks_exact(4)
        .map(|c|
            f32::from_le_bytes(c.try_into().unwrap()))
        .collect()
}

fn to_i32(b: &[u8]) -> Vec<i32> {
    b.chunks_exact(4)
        .map(|c| i32::from_le_bytes(c.try_into().unwrap()))
        .collect()
}

impl From<api::YoloPacket> for YoloMessage {

    fn from(value: api::YoloPacket) -> Self {

        let jpeg = decode_jpeg(value.jpeg_bytes);

        YoloMessage{
            frame_id: value.frame_id,
            timestamp_ms: value.timestamp_ms,
            jpeg,
            confidences: to_f32(&value.confidences),
            class_ids: to_i32(&value.class_ids),
            boxes: to_f32(&value.boxes)
        }
    }
}

impl From<api::SensorPacket> for SensorMessage {
    fn from(value: api::SensorPacket) -> Self {
        SensorMessage {
            distance_mm: value.distance_mm
                .chunks_exact(2)
                .map(|c| i16::from_le_bytes(c.try_into().unwrap()))
                .collect(),
            range_sigma_mm: value.range_sigma_mm
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes(c.try_into().unwrap()))
                .collect(),
            target_status: value.target_status
        }
    }
}


impl TryFrom<api::Packet> for protocol::Message {
    type Error = NoPayloadError;
    fn try_from(value: api::Packet) -> Result<Self, Self::Error> {

        let payload = value.payload
            .ok_or(NoPayloadError)?;

        match payload {
            api::packet::Payload::Yolo(packet) => {
                Ok(protocol::Message::Yolo(YoloMessage::from(packet)))
            }
            api::packet::Payload::Graph(packet) => {
                Ok(protocol::Message::Graph(GraphMessage::from(packet)))
            }
            api::packet::Payload::Sensor(packet) => {
                Ok(protocol::Message::Sensor(SensorMessage::from(packet)))
            }
            api::packet::Payload::Status(packet) => {
                Ok(protocol::Message::Status(StatusMessage { running: packet.running }))
            }
            api::packet::Payload::Move(packet) => {
                // Unbekannte Richtungen (z.B. neuere Proto-Version) werden wie ein leeres Paket verworfen.
                let direction = match api::MoveDirection::try_from(packet.direction) {
                    Ok(api::MoveDirection::MoveLeft) => MoveDirection::Left,
                    Ok(api::MoveDirection::MoveRight) => MoveDirection::Right,
                    Ok(api::MoveDirection::MoveStop) => MoveDirection::Stop,
                    Err(_) => return Err(NoPayloadError),
                };
                Ok(protocol::Message::Move(direction))
            }
        }
    }
}

