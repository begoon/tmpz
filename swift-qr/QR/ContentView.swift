import AVFoundation
import CodeScanner
import SwiftUI

struct ContentView: View {
    @State private var isShowingAbout = false

    @State var scannedData: String = ""

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
                    Button("About") { isShowingAbout = true }
                        .sheet(isPresented: $isShowingAbout) {
                            Text("Ha?")
                            Button("Dismiss") { isShowingAbout = false }
                        }
                    Text(message)
                }
        }.frame(height: 100)
        Spacer()
        if scannedData.hasPrefix("http") {
            Link(destination: URL(string: scannedData)!, label: {
                Text(scannedData)
            })
        } else {
            Text(scannedData)
        }
        VStack {
            Spacer()
            Image(systemName: "globe").imageScale(.large).symbolEffect(
                .bounce,
                options: .repeat(100)
            )
            Text(message)
            Spacer()
        }
        .frame(maxHeight: .infinity, alignment: .top)
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

#Preview {
    ContentView()
}
