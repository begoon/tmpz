import Foundation
import Network

Task {
    let url = CommandLine.arguments[1]
    print("url: \(url)")

    let socket = WebSocket(url: url)
    await socket.start()
    
    await socket.send(.text("como estas!"))
    
    for try await event in socket.readStream {
        print(event)
        try await Task.sleep(nanoseconds: 1_000_000_000 * 2)
        await socket.send(.text("aloha! [\(Date())]"))
    }
}

RunLoop.main.run()

public final actor WebSocket: Sendable {
    public let readStream: AsyncStream<WebSocketMessage>
    
    private let readStreamContinuation: AsyncStream<WebSocketMessage>.Continuation
    private let connection: NWConnection
    private let socketQueue: DispatchQueue
    
    public let uuid = UUID()
    
    public init(url: String) {
        let url = URL(string: url)!
        let socketQueue = DispatchQueue(label: "-")
        
        let parameters: NWParameters = NWParameters.tls
        
        let wssOptions = NWProtocolWebSocket.Options()
        parameters.allowLocalEndpointReuse = true
        parameters.defaultProtocolStack.applicationProtocols.insert(wssOptions, at: 0)
        
        self.connection = NWConnection(to: .url(url), using: parameters)
        self.socketQueue = socketQueue
        
        let readStream = AsyncStream<WebSocketMessage>.makeStream()
        self.readStream = readStream.stream
        self.readStreamContinuation = readStream.continuation
    }
    
    public func start() {
        self.connection.start(queue: self.socketQueue)
        self.read()
    }
    
    public func send(_ message: WebSocketMessage) async {
        self.connection.send(content: message.data, contentContext: message.context, completion: .contentProcessed { error in
            if let error = error {
                print("send error: \(error)")
            }
        })
    }
    
    public func close(_ code: NWProtocolWebSocket.CloseCode) {
        self.error(code: code)
    }
    
    private func error(code: NWProtocolWebSocket.CloseCode? = nil) {
        self.readStreamContinuation.finish()
        
        Task { [weak self] in
            await self?.send(.close(code ?? .protocolCode(.abnormalClosure)))
            self?.connection.cancel()
        }
    }
    
    private nonisolated func read() {
        self.connection.receiveMessage { [weak self] content, contentContext, isComplete, error in
            Task {
                if let content {
                    self?.readStreamContinuation.yield({
                        if let contentContext,
                           let wssContext = contentContext.protocolMetadata.first(where: { $0 is NWProtocolWebSocket.Metadata }) {
                            let metaData = wssContext as! NWProtocolWebSocket.Metadata
                            switch metaData.opcode {
                            case .binary:
                                return .binaryMessage(content)
                            case .text:
                                let str = String(decoding: content, as: UTF8.self)
                                return .text(str)
                            case .close:
                                return .close(metaData.closeCode)
                            default:
                                break
                            }
                        }
                        return .binaryMessage(content)
                    }())
                } else if let error {
                    print("read error: \(error)")
                }
            }
            if error == nil {
                self?.read()
            }
        }
    }
}

@frozen public enum WebSocketMessage: Sendable {
    case binaryMessage(_ data: Data)
    case text(_ string: String)
    case close(_ code: NWProtocolWebSocket.CloseCode)
    
    internal var context: NWConnection.ContentContext {
        let metadata: NWProtocolWebSocket.Metadata
        switch self {
        case .binaryMessage:
            metadata = NWProtocolWebSocket.Metadata(opcode: .binary)
        case .text:
            metadata = NWProtocolWebSocket.Metadata(opcode: .text)
        case .close(let code):
            metadata = NWProtocolWebSocket.Metadata(opcode: .close)
            metadata.closeCode = code
        }
        return NWConnection.ContentContext(identifier: UUID().uuidString, metadata: [metadata])
    }

    internal var data: Data {
        switch self {
        case let .binaryMessage(data):
            data
        case let .text(string):
            string.data(using: .utf8)!
        default:
            Data()
        }
    }
}
