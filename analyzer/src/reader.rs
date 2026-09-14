use prost::Message;
use zune_jpeg::JpegDecoder;
use zune_jpeg::zune_core::bytestream::ZCursor;
use std::error::Error;
use std::io::{BufReader, Read};
use std::net::{TcpListener, TcpStream};
use std::sync::mpsc::Sender;

/// Includes the data structures from the packets.proto file
pub mod packets {
    include!(concat!(env!("OUT_DIR"), "/packets.rs"));
}


/// Read the packet from the TCP-Stream
fn read_packet_from_buffer(
    buffer: &mut BufReader<&TcpStream>, 
) -> Result<packets::Packet, Box<dyn Error>> {
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
    let packet = packets::Packet::decode(&packet_buf[..])?;

    Ok(packet)
}

struct Jpeg {
    data: Vec<u8>,
    width: usize,
    height: usize
}

fn decode_jpeg(jpeg_bytes: Vec<u8>) -> Result<Jpeg, Box<dyn Error>> {

    let mut cursor = ZCursor::new(jpeg_bytes);
    let mut decoder = JpegDecoder::new(cursor);

    decoder.decode_headers()?;
    let (width, height) = decoder.dimensions().unwrap();
    let data = decoder.decode()?;

    Ok(Jpeg {data, width, height})
}





/// Spawn a new thread to receive data from the EyeCam-Device
pub fn spawn_eyecam_reader(tx: Sender<packets::Packet>) {
    std::thread::spawn(move || {

        let listener = TcpListener::bind("127.0.0.1:6969").expect("Unable to bind TCP listener");
        for stream in listener.incoming() {
            // Get the stream and open a new buffer reader
            let stream = stream.unwrap();
            let mut buf_reader = BufReader::new(&stream);
            println!("Connection established!");

            loop {
                let packet = read_packet_from_buffer(&mut buf_reader);

                match packet {
                    Ok(packet) => tx.send(packet).unwrap(),
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