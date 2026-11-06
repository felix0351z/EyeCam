use std::fs::{self, File};
use std::io::{self, BufWriter, Write};
use std::path::Path;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use chrono::Local;

const LOG_DIR: &str = "logs";
const FLUSH_INTERVAL: Duration = Duration::from_secs(1);

/// Schreibt empfangene Protobuf-Pakete unverändert in eine Binärdatei.
///
/// Format pro Eintrag: [u64 Empfangszeit in ms, BE][u32 Länge, BE][Paket-Bytes]
pub struct PacketLogger {
    writer: BufWriter<File>,
    last_flush: Instant,
}

impl PacketLogger {
    pub fn new() -> io::Result<Self> {
        fs::create_dir_all(LOG_DIR)?;
        let filename = Local::now().format("eyecam_%Y-%m-%d_%H-%M-%S.bin").to_string();
        let path = Path::new(LOG_DIR).join(filename);
        let file = File::create_new(&path)?;
        println!("Logging packets to {}", path.display());

        Ok(Self { writer: BufWriter::new(file), last_flush: Instant::now() })
    }

    pub fn log(&mut self, packet: &[u8]) -> io::Result<()> {
        let received_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        self.writer.write_all(&received_ms.to_be_bytes())?;
        self.writer.write_all(&(packet.len() as u32).to_be_bytes())?;
        self.writer.write_all(packet)?;

        // Nicht bei jedem Paket flushen, aber regelmäßig, da der Thread beim
        // Beenden der App ohne Drop abgebrochen wird.
        if self.last_flush.elapsed() >= FLUSH_INTERVAL {
            self.flush()?;
        }
        Ok(())
    }

    pub fn flush(&mut self) -> io::Result<()> {
        self.last_flush = Instant::now();
        self.writer.flush()
    }
}
