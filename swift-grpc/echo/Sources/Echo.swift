import ArgumentParser

@main
struct Echo: AsyncParsableCommand {
  static let configuration = CommandConfiguration(
    commandName: "echo",
    subcommands: [Serve.self, Greet.self],
  )
}
