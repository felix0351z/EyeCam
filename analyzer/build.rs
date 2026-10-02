fn main() -> Result<(), Box<dyn std::error::Error>> {
    prost_build::compile_protos(&["proto/packets.proto"], &["proto/"])?;
    Ok(())
}