// swift-tools-version: 6.1
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "http-client",
    platforms: [.macOS(.v10_15)],
    dependencies: [
        .package(url: "https://github.com/Alamofire/Alamofire", from: "5.6.4"),
    ],
    targets: [
        .executableTarget(
            name: "http-client",
            dependencies: ["Alamofire"],
            path: ".",
            sources: ["main.swift"],
            swiftSettings: [
                .unsafeFlags(["-enable-upcoming-feature", "StrictConcurrency"]),
            ]
        ),
        .testTarget(
            name: "http-client-tests",
            dependencies: ["http-client"],
            path: "tests"
        ),
    ],
)
