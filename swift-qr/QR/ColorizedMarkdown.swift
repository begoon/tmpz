import Foundation
import SwiftUI

func colorizedMarkdown(_ markdown: String) throws -> AttributedString {
    var attributed = try AttributedString(markdown: markdown, including: \.color)
    for run in attributed.runs {
        guard let name = run[ColorNameAttribute.self] else { continue }
        let color = colorFrom(name: name)
        print(name, color ?? "?")
        if let color = color {
            attributed[run.range].foregroundColor = color
        }
    }
    return attributed
}

struct ColorNameAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = String
    static let name = "color"

    static func decodeMarkdown(from markdown: String) throws -> Value {
        return markdown.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

extension AttributeScopes {
    struct ColorAttribute: AttributeScope {
        let swiftUI: SwiftUIAttributes
        let foundation: FoundationAttributes

        var color: ColorNameAttribute
    }

    var color: ColorAttribute.Type { ColorAttribute.self }
}

private func colorFrom(name: String) -> Color? {
    switch name.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
    case "red": return .red
    case "green": return .green
    case "blue": return .blue
    case "yellow": return .yellow
    case "orange": return .orange
    case "purple": return .purple
    case "pink": return .pink
    case "black": return .black
    case "white": return .white
    case "gray": return .gray
    case "cyan": return .cyan
    case "mint": return .mint
    case "indigo": return .indigo
    case "teal": return .teal
    default:
        print("⚠️ unknown color name '\(name)'")
        return nil
    }
}
