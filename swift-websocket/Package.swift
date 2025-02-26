// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "ws-nwconnection",
    platforms: [.macOS(.v10_15)],
    targets: [.executableTarget(name: "ws", path: ".")] 
)
