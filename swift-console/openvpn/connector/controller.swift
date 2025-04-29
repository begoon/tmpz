import SwiftUI

struct ConsoleView: View {
    @Binding public var content: String

    var body: some View {
        VStack {
            ScrollViewReader { proxy in
                ScrollView {
                    Text(self.content)
                        .font(.system(size: 10))
                        .font(.system(.body, design: .monospaced))
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .textSelection(.enabled)
                        .id("bottom")
                }
                .frame(minWidth: 600, minHeight: 100)
                .onChange(of: self.content) { _, _ in
                    withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
                }
            }
        }
    }
}

extension NSWindow {
    private func hide() { orderOut(nil) }
    private func show() { makeKeyAndOrderFront(nil) }
    func visibility(_ visible: Bool) {
        visible ? show() : hide()
    }
}

enum ConnectionState {
    case disconnected
    case connected
    case connecting
}

@main
struct OTP: App {
    init() {
        temporaryCredentialFilename = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        processIdentifier = 0
    }

    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    @State private var state: ConnectionState = .disconnected

    @State private var ip: String = "..."

    @State private var consoleVisible: Bool = false

    @State public var console: String = ""

    @State private var processIdentifier: Int32

    @State private var temporaryCredentialFilename: URL

    func visibility(_ visible: Bool) {
        NSApp.windows.filter { $0.className == "SwiftUI.AppKitWindow" }.forEach { window in window.visibility(visible) }
    }

    let icons: [ConnectionState: String] = [
        .disconnected: "network.slash",
        .connected: "network",
        .connecting: "cable.connector.video",
    ]

    func updateIP() {
        Task {
            self.ip = try await fetchIP()
            print("\(self.ip)")
            self.console += "\(self.ip)\n"
        }
    }

    var body: some Scene {
        Window("VPN/OTP", id: "VPN/OTP") {
            ConsoleView(content: self.$console)
                .onAppear {
                    print("onAppear()")
                    self.updateIP()
                    self.visibility(false)
                    for window in NSApp.windows.filter({ $0.className == "SwiftUI.AppKitWindow" }) {
                        window.standardWindowButton(.closeButton)?.isEnabled = false
                        print(
                            "window \(window.identifier?.rawValue ?? "?")",
                            "visible=\(window.isVisible)",
                            "restorable=\(window.isRestorable)"
                        )
                        window.isRestorable = false
                    }
                }
                .onChange(of: self.consoleVisible) { before, visible in
                    print("onChange() visibility from", before, visible)
                    self.visibility(visible)
                }
        }
        MenuBarExtra("-", systemImage: icons[state]!) {
            Text(self.ip).bold()
            if self.state == .connected {
                Button("Stop") { self.kill() }
            } else {
                Button("Start") {
                    do {
                        let command = try openvpnCommand()
                        self.start(command)
                        self.state = .connecting
                        print("CONNECTING")
                        if self.console.last != "\n" { self.console += "\n" }
                        self.console += "CONNECTING\n"
                    } catch {
                        print(error.localizedDescription)
                        if self.console.last != "\n" { self.console += "\n" }
                        self.console += "ERROR: \(error.localizedDescription)"
                    }
                }
            }
            Toggle("Console", isOn: self.$consoleVisible)
            if state == .disconnected {
                Button("Quit") {
                    NSApplication.shared.terminate(nil)
                }.keyboardShortcut("q")
            }
        }
    }

    func start(_ command: String) {
        let args = command.split(separator: " ").map { String($0) }

        print("COMMAND: \(command)")
        console += "COMMAND: \(command)\n"

        let process = Process()
        process.executableURL = URL(fileURLWithPath: args.first!)
        process.arguments = Array(args.dropFirst())

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        process.terminationHandler = { process in
            let reason = (process.terminationReason == .exit) ? "exit" : "uncaught signal"
            DispatchQueue.main.async {
                print("process exited with \(process.terminationStatus) due to \(reason)")
                if self.console.last != "\n" { self.console += "\n" }
                self.console += "process exited with \(process.terminationStatus) due to \(reason)\n"
                removeCredentialsFile()
                self.state = .disconnected
            }
        }

        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if let text = String(data: data, encoding: .utf8), !text.isEmpty {
                print(text, terminator: "")
                DispatchQueue.main.async {
                    if self.console.last != "\n" { self.console += "\n" }
                    console += text
                }
                if text.contains("Initialization Sequence Completed") {
                    DispatchQueue.main.async {
                        removeCredentialsFile()
                        print("CONNECTED")
                        if self.console.last != "\n" { self.console += "\n" }
                        self.console += "CONNECTED\n"
                        self.updateIP()
                        self.state = .connected
                    }
                }
                if text.contains("SIGTERM") {
                    DispatchQueue.main.async {
                        removeCredentialsFile()
                        print("DISCONNECTED")
                        if self.console.last != "\n" { self.console += "\n" }
                        self.console += "DISCONNECTED\n"
                        self.updateIP()
                        self.state = .disconnected
                    }
                }
            }
        }

        do {
            try process.run()
            processIdentifier = Int32(process.processIdentifier)
            print("process started \(processIdentifier)")
            if console.last != "\n" { console += "\n" }
            console += "process started \(processIdentifier)\n"
        } catch {
            print("process error: \(error.localizedDescription)")
            if console.last != "\n" { console += "\n" }
            console += "process error: \(error.localizedDescription)\n"
            removeCredentialsFile()
        }
    }

    func kill() {
        print("killing process \(processIdentifier)")

        let killer = Process()

        let command = "/usr/bin/sudo -S /bin/kill \(processIdentifier)"
        print("COMMAND: \(command)")

        let args = command.split(separator: " ").map { String($0) }

        killer.executableURL = URL(fileURLWithPath: args.first!)
        killer.arguments = Array(args.dropFirst())

        do {
            try killer.run()
        } catch {
            print("ERROR: /bin/kill: \(error.localizedDescription)")
            if console.last != "\n" { console += "\n" }
            console += error.localizedDescription + "\n"
        }
    }

    func openvpnCommand() throws -> String {
        let account = try Account(from: AccountsFilename)

        let credentials = account.username + "\n" + account.otp + "\n"

        try credentials.write(to: temporaryCredentialFilename, atomically: true, encoding: .utf8)
        print("credentials written to \(temporaryCredentialFilename.path)")

        let label = account.label
        let command = [
            "/usr/bin/sudo", "-S",
            "/opt/homebrew/sbin/openvpn",
            "--config", ConfigDirectory.appendingPathComponent(label + ".ovpn").path,
            "--auth-nocache",
            "--auth-user-pass", temporaryCredentialFilename.path,
        ].joined(separator: " ")

        print("\(command)")
        console += "\(command)\n"
        return command
    }

    func removeCredentialsFile() {
        if !FileManager.default.fileExists(atPath: temporaryCredentialFilename.path) { return }
        print("delete temporary credentials file \(temporaryCredentialFilename.path)")
        if console.last != "\n" { console += "\n" }
        console += "delete temporary credentials file \(temporaryCredentialFilename.path)\n"
        do {
            try FileManager.default.removeItem(at: temporaryCredentialFilename)
        } catch {}
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return false
    }
}

func fetchIP() async throws -> String {
    debugPrint("BEFORE: ip")
    guard let url = URL(string: "https://api.ipify.org") else { throw URLError(.badURL) }
//    let session = URLSession(configuration: .ephemeral)
    let (data, _) = try await URLSession.shared.data(from: url)
    debugPrint("AFTER: ip")
    return String(data: data, encoding: .utf8)!
}
