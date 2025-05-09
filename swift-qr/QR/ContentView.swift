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

    var body: some View {
        NavigationStack {
            Text("QR code scanner").bold()
                .toolbar {
                    Button("QR") { isShowingScanner = true }
                    Button("About") { isShowingAbout = true }
                        .sheet(isPresented: $isShowingAbout) {
                            Text("Ha?")
                            Button("Dismiss") { isShowingAbout = false }
                        }
                    Text(message)
                }
                .sheet(isPresented: self.$isShowingScanner) {
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
            Image(systemName: "globe").imageScale(.large).symbolEffect(.pulse)
            Text(message)
            Spacer()
        }
        .frame(maxHeight: .infinity, alignment: .top)
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

#Preview {
    ContentView()
}
