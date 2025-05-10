import SwiftUI

struct WebSocketView: View {
    @State private var webSocketTask: URLSessionWebSocketTask?
    @State private var receivedMessage: String = "No message yet"
    @State private var messageToSend: String = ""
    @State private var isConnected = false

    var body: some View {
        VStack(spacing: 20) {
            Text("Received: \(receivedMessage)")
                .padding()

            TextField("Enter message", text: $messageToSend)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding(.horizontal)

            HStack(spacing: 20) {
                Button("Connect") {
                    connectWebSocket()
                }
                .disabled(isConnected)

                Button("Send") {
                    sendMessage()
                }
                .disabled(!isConnected || messageToSend.isEmpty)

                Button("Disconnect") {
                    disconnectWebSocket()
                }
                .disabled(!isConnected)
            }
        }
        .padding()
    }

    func connectWebSocket() {
        guard let url = URL(string: "wss://ws.ifelse.io") else { return }

        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true
        receiveMessage()
    }

    func sendMessage() {
        let message = URLSessionWebSocketTask.Message.string(messageToSend)
        webSocketTask?.send(message) { error in
            if let error = error {
                print("WebSocket sending error: \(error)")
            }
        }
        messageToSend = ""
    }

    func receiveMessage() {
        webSocketTask?.receive { result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    DispatchQueue.main.async {
                        receivedMessage = text
                    }
                default:
                    break
                }
                receiveMessage() // Keep listening
            case .failure(let error):
                print("WebSocket receiving error: \(error)")
                DispatchQueue.main.async {
                    isConnected = false
                }
            }
        }
    }

    func disconnectWebSocket() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        isConnected = false
    }
}
