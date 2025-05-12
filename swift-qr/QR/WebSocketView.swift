import Foundation
import SwiftUI

struct WebSocketView: View {
    @State private var webSocketTask: URLSessionWebSocketTask?
    @State private var receivedMessage: String = ""
    @State private var messageToSend: String = ""
    @State private var isConnected = false

    var endpoint = "wss://ws.ifelse.io"

    var body: some View {
        VStack(spacing: 20) {
            Text("→ \(receivedMessage.lowercased())")
                .frame(maxWidth: .infinity, alignment: .leading).padding()

            TextField("", text: $messageToSend)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding(.horizontal)
                .disableAutocorrection(true)
                .autocapitalization(.none)
                .keyboardType(.default)

            Link(destination: URL(string: endpoint.replacingOccurrences(of: "wss://", with: "https://"))!, label: { Text(endpoint) })

            HStack(spacing: 20) {
                Button("Connect") {
                    connectWebSocket()
                }
                .disabled(isConnected)
                .buttonStyle(.borderedProminent)

                Button("Send") {
                    sendMessage()
                }
                .disabled(!isConnected || messageToSend.isEmpty)
                .buttonStyle(.borderedProminent)

                Button("Disconnect") {
                    disconnectWebSocket()
                }
                .disabled(!isConnected)
                .buttonStyle(.borderedProminent)
            }
        }
    }

    func connectWebSocket() {
        guard let url = URL(string: endpoint) else { return }

        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true

        Task {
            await receiveMessage()
        }
    }

    func sendMessage() {
        guard let task = webSocketTask else { return }

        let message = URLSessionWebSocketTask.Message.string(messageToSend)
        task.send(message) { error in
            if let error = error {
                print("send error: \(error)")
            }
        }
        messageToSend = ""
    }

    @MainActor
    func receiveMessage() async {
        guard let task = webSocketTask else { return }

        do {
            while true {
                let message = try await task.receive()
                switch message {
                case .string(let text):
                    receivedMessage = text
                case .data(let data):
                    receivedMessage = "<- binary data: \(data.count) bytes"
                @unknown default:
                    receivedMessage = "<- unknown type"
                }
            }
        } catch {
            isConnected = false
        }
    }

    func disconnectWebSocket() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        isConnected = false
    }
}

#Preview {
    WebSocketView()
}
