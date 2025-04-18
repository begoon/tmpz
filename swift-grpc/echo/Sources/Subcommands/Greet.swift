import ArgumentParser
import GRPCCore
import GRPCNIOTransportHTTP2
import GRPCProtobuf

struct Greet: AsyncParsableCommand {
  static let configuration = CommandConfiguration()

  @Option(help: "The port to connect on")
  var port: Int = 31415

  @Option(help: "The person to greet")
  var name: String = ""

  func run() async throws {
    try await withGRPCClient(
      transport: .http2NIOPosix(
        target: .ipv4(host: "127.0.0.1", port: self.port),
        transportSecurity: .plaintext
      )
    ) { client in
      let echoer = Echo_Echoer.Client(wrapping: client)
      let reply = try await echoer.greet(.with { $0.name = self.name })
      print(reply.message)
    }
  }
}
