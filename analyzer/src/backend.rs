use std::error::Error;
use std::io::{BufReader, Read};
use std::net::{TcpListener, TcpStream};
use crossbeam_channel::Sender;
use prost::Message;
use zune_jpeg::JpegDecoder;
use zune_jpeg::zune_core::bytestream::ZCursor;
use crate::backend::protocol::{GraphMessage, GraphValue, YoloMessage};

/// Datenstrukturen von der packets.proto Datei importieren.
/// Diese beinhalten die Kommunikationsstruktur zwischen EyeCam und dem Analyzer.
mod api {
    include!(concat!(env!("OUT_DIR"), "/packets.rs"));
}


/// Datenstrukturen für die Kommunikation zwischen Backend und Bevy-UI
pub mod protocol {

    #[derive(Clone, PartialEq)]
    pub enum Message {
        Yolo(YoloMessage),
        Graph(GraphMessage)
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

    #[derive(Copy, Clone, PartialEq)]
    pub struct GraphValue {
        pub name: i32,
        pub value: f32,
    }
}



/// Error-Typ, falls keine Payload mit dem Packet übertragen wird.
#[derive(Debug, Clone)]
pub struct NoPayloadError;

impl std::fmt::Display for NoPayloadError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "Keine Payload im Packet vorhanden!")
    }
}

/// Implementationen der Traits
/// für die Konvertierung zwischen API und dem Channel Protokoll.
impl From<api::GraphValue> for GraphValue {
    fn from(value: api::GraphValue) -> Self {
        GraphValue { name: value.name, value: value.value, }
    }
}
impl From<api::GraphPacket> for GraphMessage {
    fn from(value: api::GraphPacket) -> Self {
        GraphMessage {
            frame_id: value.frame_id,
            graphs: value.graphs.into_iter()
                .map(GraphValue::from)
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
        }
    }
}


/// Dekodiere ein Bild
/// Bytes kommen von der API / EyeCam
fn decode_jpeg(jpeg_bytes: Vec<u8>) -> protocol::Jpeg {

    let cursor = ZCursor::new(jpeg_bytes);
    let mut decoder = JpegDecoder::new(cursor);

    decoder.decode_headers()
        .expect("Failed to decode JPEG headers");

    let (width, height) = decoder.dimensions()
        .expect("No dimensions");

    let rgb = decoder.decode()
        .expect("Failed to decode Jpeg");

    let rgba: Vec<u8> = rgb
        .chunks_exact(3)
        .flat_map(|p| [p[0], p[1], p[2], 255])
        .collect();

    protocol::Jpeg {data: rgba, width, height}
}

/// Lese ein Packet von dem TCP Stream
fn read_packet_from_buffer(
    buffer: &mut BufReader<&TcpStream>,
) -> Result<api::Packet, Box<dyn Error>> {
    // Length of the packet size.
    // This is an u32 and has therefore exactly 4 bytes.
    let mut len_buf = [0u8; 4];

    // Read the length of the packet
    // If not receivable, the connection is closed, so break.
    buffer.read_exact(&mut len_buf)?;
    let size = u32::from_be_bytes(len_buf) as usize;

    // Now let's read the packet payload
    let mut packet_buf = vec![0u8; size];
    buffer.read_exact(&mut packet_buf)?;

    // Use prost to deserialize the packet
    let packet = api::Packet::decode(&packet_buf[..])?;

    Ok(packet)
}

/// Spawn a new thread to receive data from the EyeCam-Device
pub fn spawn_eyecam_receiver(tx: Sender<protocol::Message>) {
    std::thread::spawn(move || {

        let listener = TcpListener::bind("192.168.178.100:6969").expect("Unable to bind TCP listener");
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
                    Err(error) => {
                        eprintln!("Connection failure: {error}, retry in 2s");
                        break;
                    },
                    //TODO: Sleep 2 seconds
                }
            }
        }
    });
}

