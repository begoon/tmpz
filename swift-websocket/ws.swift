import Foundation

class WebSocketClient {
    private var webSocketTask: URLSessionWebSocketTask?
    private let session = URLSession(configuration: .default)
    private let url: URL

    init(url: String) {
        self.url = URL(string: url)!
    }
    
    func connect() {
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        receiveMessages()
    }
    
    func sendMessage(_ message: String) {
        let textMessage = URLSessionWebSocketTask.Message.string(message)
        webSocketTask?.send(textMessage) { error in
            if let error = error {
                print("sending message: \(error)")
            }
        }
    }
    
    private func receiveMessages() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    print("received: \(text)")
                default:
                    break
                }
                self?.receiveMessages()
            case .failure(let error):
                print("receiving message: \(error)")
            }
        }
    }
    
    func close() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
    }
}

func main() {
    guard CommandLine.arguments.count > 1 else {
        let exe = CommandLine.arguments[0].split(separator: "/").last!
        print("usage: \(exe) <websocket-url>")
        return
    }
    
    let url = CommandLine.arguments[1]
    let client = WebSocketClient(url: url)
    client.connect()
    
    print("connected to \(url)")
    
    while let input = readLine() {
        if input.lowercased() == "." {
            client.close()
            break
        }
        client.sendMessage(input)
    }
}

main()

