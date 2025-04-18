import ArgumentParser
import GRPCCore
import GRPCNIOTransportHTTP2
import GRPCProtobuf
import NIOCore 

struct Health: AsyncParsableCommand {
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
      let reply = try await ingress.health(Ingress_HealthRequest())
      print("health: \(reply)")
    }
  }
}
