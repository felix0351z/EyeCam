use std::vec::Vec;
use std::io::{BufReader, Read};
use std::net::TcpListener;
use std::sync::mpsc::Sender;

#[derive(Clone)]
pub struct EyeCamData {
    pub graphs: Vec<Graph>
}


#[derive(Copy, Clone)]
pub struct Graph {
    pub label: GraphLabel,
    pub value: f32
}

#[derive(Eq, PartialEq, Copy, Clone)]
pub enum GraphLabel {
    ZoneLeft,
    ZoneMiddle,
    ZoneRight,
}

impl TryFrom<i32> for GraphLabel {
    type Error = &'static str;

    fn try_from(value: i32) -> Result<Self, Self::Error> {

        match value {
            0 => Ok(GraphLabel::ZoneLeft),
            1 => Ok(GraphLabel::ZoneMiddle),
            2 => Ok(GraphLabel::ZoneRight),
            _ => { Err("Invalid graph label") }
        }
    }
}

impl Graph {
    pub fn new(data: &[u8]) -> Graph {
        let label = i32::from_le_bytes(data[0..4].try_into().unwrap());
        let value = f32::from_le_bytes(data[4..8].try_into().unwrap());

        Graph {
            label: GraphLabel::try_from(label).unwrap(),
            value
        }
    }


}



pub fn spawn_eyecam_reader(tx: Sender<EyeCamData>) {
    std::thread::spawn(move || {

        let listener = TcpListener::bind("127.0.0.1:6969").expect("Unable to bind TCP listener");
        for stream in listener.incoming() {
            let stream = stream.unwrap();
            let mut buffer = [0u8; 24];
            let mut buf_reader = BufReader::new(&stream);

            println!("Connection established!");
            loop {
                match buf_reader.read_exact(&mut buffer) {
                    Ok(()) => {

                        let mut iterator = 0;
                        let length = 8;
                        let mut output : Vec<Graph> = Vec::new();

                        for _ in 0..3 {
                            output.push(Graph::new(buffer[iterator..iterator+8].try_into().unwrap()));
                            iterator += length;
                        }

                        // Send data to stream
                        tx.send(EyeCamData { graphs: output }).unwrap();
                    }

                    Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => {
                        // Connection closed
                        break;
                    },
                    Err(e) => println!("Error: {:?}", e)
                }


            }
        }





    });
}



