import ArgumentParser
import GRPCCore
import GRPCNIOTransportHTTP2
import GRPCProtobuf
import NIOCore 
import SwiftProtobuf

struct Logging: AsyncParsableCommand {
  static let configuration = CommandConfiguration()

  @Option(help: "The port to connect to")
  var port: Int = 443

  @Option(help: "The host to connect to")
  var host: String = "127.0.0.1"

  @Option(help: "TLS")
  var tls: Bool = true 

  func run() async throws {
    try await withGRPCClient(
      transport: .http2NIOPosix(
        target: .dns(host: self.host, port: self.port),
        transportSecurity: self.tls ? .tls : .plaintext
      )
    ) { client in
      let ingress = Ingress_Ingress.Client(wrapping: client)
      let requestMetadata: Metadata = [
        "client-id": "-client_id-", 
        "x-api-key": "-secret_key-"
      ]
      
      let messages = [ 
        Ingress_LoggingRequest.with { 
          $0.data = {
              var s = Google_Protobuf_Struct()
              s.fields = [
                  "name": "-name-",
                  "age": 100,
                  "active": true,
              ]
              return s
          }()
        },
        Ingress_LoggingRequest.with { 
          $0.data = {
              var s = Google_Protobuf_Struct()
              s.fields = ["info": "abc"]
              return s
          }()
        },
      ]

      let reply = try await ingress.logging(metadata: requestMetadata) { writer in
        try await writer.write(contentsOf: messages)
      }
      print("logging: \(reply)")
    }
  }
}
