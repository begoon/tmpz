import AVFoundation
import CodeScanner
import Foundation
import RegexBuilder
import SwiftUI
import UIKit
import UniformTypeIdentifiers

struct Storage: Codable {
    var scannedData: String = ""
    var when: Date = .init()
}

struct ContentView: View {
    @State private var showAbout = false

    @State var scannedData: String = [
        "https://google.com",
        "https://github.com",
    ].joined(separator: " ")

    @State var storageURL: URL?

    func handleScan(result: Result<ScanResult, ScanError>) {
        switch result {
        case .success(let scanResult):
            print("scanned: \(scanResult)")
            scannedData = scanResult.string
            let storage = Storage(scannedData: scannedData)
            let data = try! JSONEncoder().encode(storage)
            storageURL = persistToDocuments(data: data, filename: "qr.json")
        case .failure(let error):
            print("scanning failed: \(error)")
            scannedData = "\(error)"
        }
    }

    func textify(_ input: String) -> AttributedString {
        var string: String = input
        if let data = Data(base64Encoded: input) {
            string = asciify(from: data)
        }
        if let markdown = try? AttributedString(markdown: string) {
            return markdown
        }
        return AttributedString(string)
    }

    func asciify(from data: Data) -> String {
        return data.map { byte -> String in
            if byte >= 0x20 && byte <= 0x7E {
                return String(UnicodeScalar(byte))
            }
            return String(format: "<%02X>", byte)
        }.joined()
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                HStack(alignment: .top) {
                    Text(textify(scannedData))
                        .padding()
                        .textSelection(.enabled)
                }.multilineTextAlignment(.leading)
            }
            HStack {
                QRButtonView(completion: handleScan)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .buttonStyle(.borderless)
                    .cornerRadius(8)
                if storageURL != nil {
                    Spacer()
                    ShareLink("Share", item: storageURL!)
                }
            }
            .padding()
            .toolbar {
                Button("About") { showAbout = true }
                    .sheet(isPresented: $showAbout) {
                        AboutView()
                    }
            }
        }
    }
}

func markdownFrom(_ input: String) -> String {
    let re = /https:\/\/[^ ]+/

    var markdown = input
    let matches = input.matches(of: re).reversed()

    for match in matches {
        let url = String(match.0)
        let markdownLink = "[\(url)](\(url))"
        if let range = markdown.range(of: url, options: .literal, range: markdown.startIndex ..< markdown.endIndex, locale: nil) {
            markdown.replaceSubrange(range, with: markdownLink)
        }
    }

    return markdown
}

let codeTypes: [AVMetadataObject.ObjectType] = [
    .aztec,
    .code128,
    .code39,
    .code39Mod43,
    .code93,
    .dataMatrix,
    .ean13,
    .ean8,
    .interleaved2of5,
    .itf14,
    .pdf417,
    .qr,
    .upce,
]

struct QRButtonView: View {
    @State private var isShowing: Bool = false

    @State var completion: (Result<ScanResult, ScanError>) -> Void
    @State var simulatedData = "https://google.com"

    var body: some View {
        Button("QR") { isShowing = true }
            .sheet(isPresented: $isShowing) {
                CodeScannerView(
                    codeTypes: codeTypes,
                    showViewfinder: true,
                    simulatedData: simulatedData,
                    completion: { result in
                        isShowing = false
                        completion(result)
                    }
                )
                Button("Close") { isShowing = false }
            }
    }
}

func persistData(_ data: Data, to storageURL: URL, with filename: String) -> URL? {
    let fileURL = storageURL.appendingPathComponent(filename)
    do {
        try FileManager.default.createDirectory(at: storageURL, withIntermediateDirectories: true, attributes: nil)
        try data.write(to: fileURL, options: .atomic)
        print("saved to: \(fileURL.path)")
    } catch {
        print("save failed: \(error)")
        return nil
    }
    return fileURL
}

func persistToDocuments(data: Data, filename: String) -> URL? {
    guard let storageURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
        print("documentDirectory:", "❌ could not locate document directory")
        return nil
    }
    return persistData(data, to: storageURL, with: filename)
}

#Preview {
    ContentView()
}
