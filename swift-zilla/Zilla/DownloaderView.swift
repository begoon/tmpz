import CryptoKit
import SwiftUI

struct DownloaderView: View {
    @State private var downloadProgress: Double = 0.0
    @State private var isDownloading = false

    @State private var sha1Hash: String = ""
    @State private var throughput: Double = 0

    @State private var downloadedBytes: Int64 = 0
    @State private var totalBytes: Int64 = 0

    @State private var startTime: Date?
    @State private var duration: TimeInterval?

    var body: some View {
        VStack(spacing: 20) {
            ProgressView(value: downloadProgress)
                .progressViewStyle(LinearProgressViewStyle())
                .padding()
            HStack {
                if isDownloading {
                    Text("\(downloadedBytes) / \(totalBytes) bytes (\(Int(downloadProgress * 100))%)")
                } else {
                    Text("\(duration ?? 0.0) seconds | (\(throughput) Mbps)")
                }
            }.font(.caption).monospacedDigit()

            HStack {
                if isDownloading {
                    Image(systemName: "arrow.clockwise").imageScale(.large).symbolEffect(.rotate)
                } else {
                    Text(sha1Hash)
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .multilineTextAlignment(.center)
                        .padding()
                }
            }.frame(height: 44)
            Button(isDownloading ? "downloading..." : "download") {
                if !isDownloading {
                    startDownload()
                }
            }
            .disabled(isDownloading)
        }
        .padding()
    }

    func startDownload() {
        guard let url = URL(string: "http://ipv4.download.thinkbroadband.com/20MB.zip") else { return }

        startTime = Date()
        print("started at:", startTime!)

        isDownloading = true
        downloadProgress = 0

        let task = URLSession.shared.downloadTask(with: url) { tempURL, _, error in
            guard let tempURL = tempURL, error == nil else {
                print("download error:", error ?? "unknown")
                return
            }
            print("->", tempURL)

            do {
                let endTime = Date()
                print("ended at:", endTime)

                let data = try Data(contentsOf: tempURL)
                let digest = Insecure.SHA1.hash(data: data)
                let sha1String = digest.map { String(format: "%02hhx", $0) }.joined()

                DispatchQueue.main.async {
                    sha1Hash = "\(sha1String)"
                    
                    duration = endTime.timeIntervalSince(startTime!)
                    print("duration: \(duration ?? -1) seconds")
                    
                    throughput = (Double(downloadedBytes) / duration!).rounded(.down) / 1024 / 1024
                    
                    isDownloading = false
                }
            } catch {
                print("file processing error:", error)
            }
        }

        Timer.scheduledTimer(withTimeInterval: 0.2, repeats: true) { timer in
            if task.countOfBytesExpectedToReceive > 0 {
                let progress = Double(task.countOfBytesReceived) / Double(task.countOfBytesExpectedToReceive)
                DispatchQueue.main.async {
                    downloadProgress = progress
                    downloadedBytes = task.countOfBytesReceived
                    totalBytes = task.countOfBytesExpectedToReceive
                }
            }

            if task.state == .completed {
                timer.invalidate()
            }
        }

        task.resume()
    }
}

#Preview {
    DownloaderView()
}
