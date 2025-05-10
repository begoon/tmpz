import Foundation
import SwiftUI

@testable import QR
import Testing

struct ColorAttributeTests {
    @Test func colorize() async throws {
        print(try! colorizedMarkdown("This is ^[in red](color: 'red')."))
        print(try! colorizedMarkdown("This is ^[unknown](color: 'abc')."))
    }
}
