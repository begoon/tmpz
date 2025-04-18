import ArgumentParser

@main
struct Ingress: AsyncParsableCommand {
  static let configuration = CommandConfiguration(
    subcommands: [Health.self, Logging.self],
  )
}
