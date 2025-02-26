import SwiftUI

@MainActor
class PingViewModel: ObservableObject {
    @Published var output: String = ""
    private var process: Process?
    private var pipe: Pipe?
    
    func startPinging() {
        process = Process()
        pipe = Pipe()
        
        guard let process = process, let pipe = pipe else { return }
        
        process.executableURL = URL(fileURLWithPath: "/sbin/ping")
        process.arguments = ["-c", "10", "google.com"]
        
        process.standardOutput = pipe
        process.standardError = pipe
        
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if let text = String(data: data, encoding: .utf8), !text.isEmpty {
                DispatchQueue.main.async {
                    self?.output.append(text)
                }
            }
        }
        
        do {
            try process.run()
        } catch {
            output.append("Failed to start ping: \(error.localizedDescription)\n")
        }
    }
    
    deinit {
        pipe?.fileHandleForReading.readabilityHandler = nil
        process?.terminate()
    }
}

struct ContentView: View {
    @StateObject var viewModel = PingViewModel()
    
    var body: some View {
        VStack {
            ScrollView {
                Text(viewModel.output)
                    .font(.system(.body, design: .monospaced))
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(minWidth: 600, minHeight: 100)
            
            Button("Start Ping") {
                viewModel.startPinging()
            }
            .padding()
        }
    }
}

@main
struct PingStreamerApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
}
