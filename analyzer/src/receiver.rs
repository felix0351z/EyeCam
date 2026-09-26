use bevy::prelude::*;
use crossbeam_channel::Receiver;
use crate::backend::protocol;
use crate::backend;

// --------------------------------------
// Plugin Setup
// --------------------------------------
pub struct ReceiverPlugin;
impl Plugin for ReceiverPlugin {
    fn build(&self, app: &mut App) {
        app
            .init_resource::<LatestYoloMessage>()
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


// --------------------------------------
// Systeme und Hilfsfunktionen
// --------------------------------------

/// Starte den TCP-Listener in einem neuen Background-Thread.
///
/// Die Kommunikation funktioniert mit einem Crossbeam-Channel,
/// wobei der Receiver im `MessageReceiver` gespeichert wird und von
/// `receive_messages` ausgelesen wird.
fn setup(mut commands: Commands) {
    let (tx, rx) = crossbeam_channel::bounded(2);
    commands.insert_resource(MessageReceiver(rx));

    backend::spawn_eyecam_receiver(tx);
}


/// Lese den Crossbeam-Channel aus.
/// Speichere immer die letzte Nachricht vom jeweiligen Typ.
fn receive_messages(
    receiver: Res<MessageReceiver>,
    mut yolo_message: ResMut<LatestYoloMessage>,
) {
    for message in receiver.0.try_iter() {
        match message {
            protocol::Message::Yolo(yolo) => yolo_message.0 = Some(yolo),
            protocol::Message::Graph(_) => {}
        }
    }
}