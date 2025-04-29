import Foundation

let UserHome = FileManager.default.homeDirectoryForCurrentUser

let ConfigDirectory = UserHome.appendingPathComponent(".otpvpn")
let AccountsFilename = ConfigDirectory.appendingPathComponent("Account.json")

struct Account: Codable {
    var label: String
    var username: String
    var password: String
    var secret: String

    private static func parse(from text: String) throws -> Account {
        do {
            return try JSONDecoder().decode(Account.self, from: Data(text.utf8))
        } catch {
            print("decode error: \(error)")
            throw error
        }
    }

    init(from text: String) throws {
        self = try Account.parse(from: text)
        print("account \(self)")
    }

    init(from fileURL: URL) throws {
        print("load account from \(fileURL.path)")
        let contents = try String(contentsOf: fileURL, encoding: .utf8)
        try self.init(from: contents)
    }

    var otp: String {
        self.password.replacingOccurrences(of: "<@>", with: totp(using: self.secret))
    }
}
