import CodeScanner
import SwiftUI

struct ContentView: View {
    @State private var isShowingAbout = false

    @State private var isShowingScanner = false

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
        case .failure(let error):
            print("scanning failed: \(error)")
        }
        isShowingScanner = false
    }

    let title = try! colorizedMarkdown(
        "^[QR](color: 'blue')" + " ~code~ " + "^[**scanner**](color: 'green')"
    )
    var body: some View {
        NavigationStack {
            Text(title).font(.largeTitle)
                .bold().toolbar {
                    Button("QR") { isShowingScanner = true }
                    Button("About") { isShowingAbout = true }
                        .sheet(isPresented: $isShowingAbout) {
                            Text("Ha?")
                            Button("Dismiss") { isShowingAbout = false }
                        }
                    Text(message)
                }
                .sheet(isPresented: $isShowingScanner) {
                    CodeScannerView(
                        codeTypes: [.qr],
                        simulatedData: "-data-",
                        completion: handleScan
                    )
                    Button("Close") { isShowingScanner = false }
                }
        }.frame(height: 100)
        Spacer()
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
        Text(try! AttributedString(markdown: "This is ^[in red](color: 'red')!", including: \.custom))
        Button("QR") { isShowingScanner = true }
            .sheet(isPresented: $isShowingScanner) {
                CodeScannerView(
                    codeTypes: [.qr],
                    simulatedData: "-data-",
                    completion: handleScan
                )
                Button("Close") { isShowingScanner = false }
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
