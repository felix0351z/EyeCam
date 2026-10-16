use crate::backend::protocol::{GraphMessage, GraphSource, GraphValue, SensorMessage, YoloMessage, Zone};
use crossbeam_channel::Sender;
use prost::Message;
use std::error::Error;
use std::io::{BufReader, Read};
use std::net::{SocketAddr, TcpListener, TcpStream};
use zune_jpeg::JpegDecoder;
use zune_jpeg::zune_core::bytestream::ZCursor;
// --------------------------------------
// Einstiegspunkt
// --------------------------------------

/// Spawne einen neuen Thread um Daten vom EyeCam-Gerät zu empfangen
pub fn spawn_eyecam_receiver(tx: Sender<protocol::Message>) {
    std::thread::spawn(move || {

        let local_ip = local_ip_address::local_ip()
            .expect("Unable to get local IP address");
        println!("Local IP: {}", local_ip);
        let socket = SocketAddr::new(local_ip, 6969);

        let listener = TcpListener::bind(socket).expect("Unable to bind TCP listener");
        for stream in listener.incoming() {
            // Get the stream and open a new buffer reader
            let stream = stream.unwrap();
            let mut buf_reader = BufReader::new(&stream);
            println!("Connection established!");

            loop {
                let packet = read_packet_from_buffer(&mut buf_reader);

                match packet {
                    Ok(packet) => {
                        // Send a new message through the channel if a payload is available.
                        if let Some(msg) = packet.try_into().ok() {
                            if tx.send(msg).is_err() {
                                break;
                            }
                        }
                    },
                    Err(_) => {
                        eprintln!("Connection closed. Waiting for new connections...");
                        break;
                    },
                }
            }
        }
    });
}

// --------------------------------------
// Funktionen
// --------------------------------------

/// Lese ein Packet von einem Bytestream aus
fn read_packet_from_buffer(
    buffer: &mut BufReader<&TcpStream>
) -> Result<api::Packet, Box<dyn Error>> {
    // Länge der Paketgröße.
    // Dieser ist vom Typ u32 und wird daher mit 4 Bytes angegeben.
    let mut len_buf = [0u8; 4];

    // Lese die Paketgröße
    buffer.read_exact(&mut len_buf)?;
    let size = u32::from_be_bytes(len_buf) as usize;

    // Paket lesen und in einem Vec-Buffer zwischenspeichern.
    let mut packet_buf = vec![0u8; size];
    buffer.read_exact(&mut packet_buf)?;

    // Packet mit prost deserializen.
    let packet = api::Packet::decode(&packet_buf[..])?;
    Ok(packet)
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
mod api {
    include!(concat!(env!("OUT_DIR"), "/packets.rs"));
}


/// Protokoll für die Kommunikation zwischen Backend und Bevy-UI
/// auf dem Crossbeam-Channel
pub mod protocol {

    #[derive(Clone, PartialEq)]
    pub enum Message {
        Yolo(YoloMessage),
        Graph(GraphMessage),
        Sensor(SensorMessage)
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
        }
    }
}

