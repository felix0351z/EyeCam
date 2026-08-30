use prost::Message;
use std::io::{BufReader, Read};
use std::net::TcpListener;
use std::sync::mpsc::Sender;

// Include the data structures from the .proto file
pub mod packets {
    include!(concat!(env!("OUT_DIR"), "/packets.rs"));
}




pub fn spawn_eyecam_reader(tx: Sender<packets::Packet>) {
    std::thread::spawn(move || {

        let listener = TcpListener::bind("127.0.0.1:6969").expect("Unable to bind TCP listener");
        for stream in listener.incoming() {
            // Get the stream and open a new buffer reader
            let stream = stream.unwrap();
            let mut buf_reader = BufReader::new(&stream);
            println!("Connection established!");

            // Length of the packet size.
            // This is an u32 and has therefore exactly 4 bytes.
            let mut len_buf = [0u8; 4];

            loop {
                // Read the length of the packet
                // If not receivable, the connection is closed, so break.
                if buf_reader.read_exact(&mut len_buf).is_err() {
                    break;
                }

                let size = u32::from_be_bytes(len_buf) as usize;

                // Now let's read the packet payload
                let mut packet_buf = vec![0u8; size];
                if buf_reader.read_exact(&mut packet_buf)
                    .is_err() { break; }

                // Use prost to deserialize the packet
                let Ok(packet) = packets::Packet::decode(&packet_buf[..]) else {
                    println!("Received invalid packet");
                    break;
                };


                // Send data to the stream
                tx.send(packet).unwrap();
            }

        }





    });
}



