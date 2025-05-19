import AVFoundation
import CodeScanner
import Foundation
import RegexBuilder
import SwiftProtobuf
import SwiftUI
import UIKit
import UniformTypeIdentifiers

struct Storage: Codable {
    var scannedData: String = ""
    var when: Date = .init()
}

struct ContentView: View {
    @State private var showAbout = false

    @State var scannedData: String = ""

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

    func ingressKioskConfig(_ bytes: Data) throws -> Iproov_Ingress_Config_KioskConfig {
        let config = try Iproov_Ingress_Config_KioskConfig(serializedBytes: bytes)
        return config
    }

    func textify(_ input: String) -> AttributedString {
        var string: String = input
        print(input)
        if let data = Data(base64Encoded: input), !data.isEmpty {
            if let kioskConfig = try? ingressKioskConfig(data) {
                if let compactJSON = try? kioskConfig.jsonString(),
                   let data = compactJSON.data(using: .utf8),
                   let object = try? JSONSerialization.jsonObject(with: data),
                   let prettyData = try? JSONSerialization.data(withJSONObject: object, options: [.prettyPrinted, .withoutEscapingSlashes]),
                   let prettyString = String(data: prettyData, encoding: .utf8)
                {
                    string = prettyString
                } else {
                    string = "\(kioskConfig)"
                }
            } else {
                string = asciify(from: data)
            }
        }
        print(string)
        if let markdown = try? AttributedString(
            markdown: string,
            options: AttributedString.MarkdownParsingOptions(interpretedSyntax: .inlineOnly
            )
        ) {
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
            VStack {
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
                HStack {
                    Button("URL") {
                        scannedData = [
                            "https://google.com",
                            "https://github.com",
                        ].joined(separator: "\n")
                    }
                    Button("Kiosk") {
                        scannedData = "CAESNAokaHR0cHM6Ly9zYW11ZWwuZGV2LmluZ3Jlc3MuaXByb292LmlvEgwtc2VjcmV0X2tleS0aZAoqd3NzOi8vc2FuZGJveC5kZXYuaW5ncmVzcy5pcHJvb3YuaW8vYnJva2VyEgdkZWZhdWx0Gid3c3M6Ly9zYW5kYm94LmRldi5pbmdyZXNzLmlwcm9vdi5pby9lcHAiBGF1dG8="
                    }
                    Spacer()
                    Button("Clear") { scannedData = "" }
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
