// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "pinger",
    platforms: [.macOS(.v11)],
    products: [.executable(name: "pinger",targets: ["pinger"])],
    targets: [.executableTarget(name: "pinger", path: ".")]
)
