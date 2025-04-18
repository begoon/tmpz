import ArgumentParser
import GRPCCore
import GRPCNIOTransportHTTP2
import GRPCProtobuf

struct Serve: AsyncParsableCommand {
  static let configuration = CommandConfiguration(abstract: "Starts a greeter server.")

  @Option(help: "The port to listen on")
  var port: Int = 31415

  func run() async throws {
    let server = GRPCServer(
      transport: .http2NIOPosix(
        address: .ipv4(host: "127.0.0.1", port: self.port),
        transportSecurity: .plaintext
      ),
      services: [Greeter()]
    )

    try await withThrowingDiscardingTaskGroup { group in
      group.addTask { try await server.serve() }
      if let address = try await server.listeningAddress {
        print("Greeter listening on \(address)")
      }
    }
  }
}

struct Greeter: Echo_Echoer.SimpleServiceProtocol {
  func greet(
    request: Echo_GreetRequest,
    context: ServerContext
  ) async throws -> Echo_GreetReply {
    var reply = Echo_GreetReply()
    let recipient = request.name.isEmpty ? "stranger" : request.name
    reply.message = "aloha, \(recipient)"
    return reply
  }
}
