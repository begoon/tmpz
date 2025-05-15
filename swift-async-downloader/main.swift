import Foundation

let sizes = ["5MB", "10MB", "20MB", "50MB", "100MB", "200MB", "512MB", "1GB", "2GB", "5GB"]
let defaultSize = sizes.first!

func downloadURL(for size: String) -> URL {
    return URL(string: "http://ipv4.download.thinkbroadband.com/\(size).zip")!
}

func formatBytes(_ bytes: Int64) -> String {
    let formatter = ByteCountFormatter()
    formatter.allowedUnits = .useKB
    return formatter.string(fromByteCount: bytes)
}

actor ProgressPrinter {
    private var progress: [Int: (received: Int64, expected: Int64)] = [:]

    func update(taskId: Int, received: Int64, expected: Int64) {
        progress[taskId] = (received, expected)
        printStatus()
    }

    let clearScreen = "\u{001B}[2J"

    private func printStatus() {
        var output = ""
        for (id, (received, expected)) in progress.sorted(by: { $0.key < $1.key }) {
            let percent = expected > 0 ? Double(received) / Double(expected) * 100 : 0
            output += String(
                format: "task %d: %@ / %@ (%.2f%%)\n",
                id,
                formatBytes(received),
                formatBytes(expected),
                percent
            )
        }
        output += "\u{001B}[\(progress.count + 1)A"
        print(output)
    }
}

class DownloadDelegate: NSObject, URLSessionDataDelegate {
    private let taskId: Int
    private let progressPrinter: ProgressPrinter
    private let verbosity: Int

    private var expectedLength: Int64 = 0
    private var receivedData = Data()
    private var continuation: CheckedContinuation<Data, Error>?

    init(taskId: Int, progressPrinter: ProgressPrinter, verbosity: Int = 0) {
        self.taskId = taskId
        self.progressPrinter = progressPrinter
        self.verbosity = verbosity
    }

    func urlSession(
        _ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse,
        completionHandler: @escaping (URLSession.ResponseDisposition) -> Void
    ) {
        expectedLength = response.expectedContentLength
        Task {
            await progressPrinter.update(taskId: taskId, received: 0, expected: expectedLength)
        }
        completionHandler(.allow)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        receivedData.append(data)
        Task {
            await progressPrinter.update(
                taskId: taskId, received: Int64(receivedData.count), expected: expectedLength
            )
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?)
    {
        if let error = error {
            continuation?.resume(throwing: error)
        } else {
            continuation?.resume(returning: receivedData)
        }
    }

    public func urlSession(_ session: URLSession, didCreateTask task: URLSessionTask) {
        if self.verbosity < 2 { return }
        print("task created: \(task.currentRequest!.url!)")
    }

    public func urlSession(
        _ session: URLSession, task: URLSessionTask,
        didFinishCollecting metrics: URLSessionTaskMetrics
    ) {
        if verbosity < 1 { return }
        print(
            metrics.transactionMetrics.map { value in
                (
                    status: ((value.response as? HTTPURLResponse)?.statusCode)!,
                    remote: value.remoteAddress!,
                    url: value.response!.url!,
                    protocol: value.networkProtocolName!,
                    received: value.countOfResponseBodyBytesReceived
                )
            }
        )
    }

    func startDownload(from url: URL) async throws -> Data {
        try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            let config = URLSessionConfiguration.ephemeral
            let session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
            session.dataTask(with: url).resume()
        }
    }
}

func main() async {
    var arguments = CommandLine.arguments

    func usage() -> Never {
        print(
            """
            usage: \(arguments[0]) -v concurrent_downloads [size]

            concurrent_downloads: number of concurrent downloads
            size: size of the download (default: 10MB)

            available sizes: \(sizes.joined(separator: ", "))
            default download URL: \(downloadURL(for: defaultSize))

            -v: verbosity
            -vv: more verbosity

            example: \(arguments[0]) 4 5MB
            """
        )
        exit(1)
    }

    let concurrentDownloads: Int = {
        if arguments.count > 1, let value = Int(arguments[1]), value > 0 {
            return value
        }
        usage()
    }()

    var verbosity = 0
    if arguments.contains("-v") { verbosity = 1 }
    if arguments.contains("-vv") { verbosity = 2 }

    arguments.removeAll { $0 == "-v" || $0 == "-vv" }

    let size = {
        if arguments.count <= 2 { return defaultSize }
        let size = arguments[2].uppercased()
        if sizes.contains(size) { return size }
        FileHandle.standardError.write("invalid size: \(size)".data(using: .utf8)!)
        usage()
    }()

    let progressPrinter = ProgressPrinter()
    let start = Date()

    do {
        let results: [Data] = try await withThrowingTaskGroup(of: Data.self) { group in
            for i in 1...concurrentDownloads {
                group.addTask {
                    let delegate = DownloadDelegate(
                        taskId: i, progressPrinter: progressPrinter, verbosity: verbosity
                    )
                    return try await delegate.startDownload(from: downloadURL(for: size))
                }
            }

            var downloadedData = [Data]()
            for try await result in group {
                downloadedData.append(result)
            }
            return downloadedData
        }

        let elapsed = Date().timeIntervalSince(start)
        print(String(format: "duration: %.2f seconds", elapsed))

        print("downloaded: \(formatBytes(Int64(results.reduce(0) { $0 + $1.count })))")

        let throughput = Double(results.reduce(0) { $0 + $1.count }) / elapsed
        print(String(format: "throughput: %.2f MB/s", throughput / 1024 / 1024))
    } catch {
        print("❌ \(error)")
    }
}

await main()
