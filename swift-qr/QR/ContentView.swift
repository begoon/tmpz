import AVFoundation
import CodeScanner
import SwiftUI
import UIKit
import UniformTypeIdentifiers

struct Storage: Codable {
    var scannedData: String = ""
    var when: Date = .init()
}

struct ContentView: View {
    @State private var showAbout = false

    @State var scannedData: String = "https://google.com"
    @State var storageURL: URL?

    @State private var showImporter = false

    let message: AttributedString

    init() {
        var message = try! AttributedString(markdown: "*A*loh*a!")
        if let range = message.range(of: "oh") {
            message[range].font = .body.bold()
            message[range].foregroundColor = .red
        }
        self.message = message
    }

    func handleScan(result: Result<ScanResult, ScanError>) {
        switch result {
        case .success(let scanResult):
            print("scanned: \(scanResult)")
            scannedData = scanResult.string
        case .failure(let error):
            print("scanning failed: \(error)")
            scannedData = "\(error)"
        }
    }

    let title = try! colorizedMarkdown(
        "^[QR](color: 'blue')" + " ~code~ " + "^[**scanner**](color: 'green')"
    )

    var body: some View {
        NavigationStack {
            Text(title).font(.largeTitle)
                .bold().toolbar {
                    QRButtonView(completion: handleScan)
                    Button("About") { showAbout = true }
                        .sheet(isPresented: $showAbout) {
                            AboutView()
                        }
                    Text(message)
                }
        }
        if scannedData.hasPrefix("http") {
            Link(destination: URL(string: scannedData)!, label: {
                Text(scannedData)
            })
        } else {
            Text(scannedData)
        }
        VStack {
            Spacer()
            Image(systemName: "trash").imageScale(.large).symbolEffect(
                .bounce, options: .repeat(100)
            )
            Text(message)
        }
        .frame(alignment: .top)
        HStack {
            Button("Store") {
                print("exporting")
                let storage = Storage(scannedData: self.scannedData)
                print("storage", storage)
                let data = try! JSONEncoder().encode(storage)
                self.storageURL = persistDataLocally(data: data, filename: "swift_data.json")
            }.buttonStyle(.borderedProminent)
            if self.storageURL != nil {
                let url = self.storageURL!
                ShareLink("Share", item: url)
            }
            Button("Import") {
                showImporter = true
            }
        }
        .fileImporter(
            isPresented: $showImporter,
            allowedContentTypes: [.json],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                guard let url = urls.first else { return }

                print("importing", url)
                guard url.startAccessingSecurityScopedResource() else {
                    print("unable to access file due to security restrictions")
                    return
                }
                defer { url.stopAccessingSecurityScopedResource() }

                guard FileManager.default.fileExists(atPath: url.path) else {
                    print("file not found")
                    return
                }

                do {
                    let data = try Data(contentsOf: url)
                    let storage = try JSONDecoder().decode(Storage.self, from: data)
                    print("IMPORTED", storage)
                } catch {
                    print("failed to read or parse file: \(error)")
                }
            case .failure(let error):
                print("import failed: \(error)")
            }
        }
        WebSocketView()
        DownloaderView()
        QRButtonView(completion: handleScan)
    }
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
    .upce
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
                    completion: { result in isShowing = false
                        completion(result)
                    }
                )
                Button("Close") { isShowing = false }
            }
    }
}

extension AttributeScopes {
    struct CustomAttributes: AttributeScope {
        let swiftUI: SwiftUIAttributes
        let foundation: FoundationAttributes

        struct ColorNameAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
            typealias Value = String
            static let name = "color"

            static func decodeMarkdown(from markdown: String) throws -> Value {
                return markdown.trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }

        var color: ColorNameAttribute
    }

    var custom: CustomAttributes.Type { CustomAttributes.self }
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

func persistDataLocally(data: Data, filename: String) -> URL? {
    guard let storageURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
        print("documentDirectory:", "❌ could not locate document directory")
        return nil
    }
    return persistData(data, to: storageURL, with: filename)
}

func persistDataToCloud(data: Data, filename: String) {
    print("ubiquityIdentityToken:",
          FileManager.default.ubiquityIdentityToken != nil ?
              "✅ icloud available" : "❌ icloud unavailable")

    guard let storageURL = FileManager.default.url(forUbiquityContainerIdentifier: nil) else {
        print("forUbiquityContainerIdentifier:", "❌ icloud not available")
        return
    }

    _ = persistData(data, to: storageURL, with: filename)
}

#Preview {
    ContentView()
}
