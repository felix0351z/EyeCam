use std::{error::Error, fs::{File, OpenOptions}, io::{BufWriter, Write}};

use chrono::{Timelike, Utc};
use egui::mutex::Mutex;
use serde::Serialize;

pub struct JsonLogger {
    writer: Mutex<BufWriter<File>>
}

impl JsonLogger {

    pub fn new() -> Result<Self, Box<dyn Error>> {
        let time = Utc::now();
        let filename = format!("log-{:02}-{:02}-{:-02}", time.hour(), time.minute(), time.second());

        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(filename)?;

            Ok(Self { writer: Mutex::new(
                BufWriter::new(file
            )) })
    }

    pub fn log<T: Serialize>(&self, entry: &T) -> Result<(), Box<dyn Error>> {
        let mut guard = self.writer.lock();
        
        serde_json::to_writer(&mut *guard, entry)?;
        guard.write_all(b"\n")?;
        guard.flush()?;
        Ok(())
    }


    
}