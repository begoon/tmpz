import Foundation
import SwiftData

@Model
class Note {
    var title: String
    var content: String
    var when: Date

    init(title: String, content: String) {
        self.title = title
        self.content = content
        self.when = Date()
    }
}

func returnTypeOf<Arg, Return>(of function: (Arg) async throws -> Return) -> Return.Type {
    Return.self
}

typealias FetchResult = (task: Int, N: Int)

@main
struct cli {
    static func main() async throws {
        print("current directory:", FileManager.default.currentDirectoryPath)
        let container = try ModelContainer(
            for: Note.self,
            configurations: ModelConfiguration(url: URL(fileURLWithPath: "./database.store"))
        )

        let context = container.mainContext
        let note = Note(title: "👍 aloha", content: "thread: \(Task.currentPriority) \(Date())")
        context.insert(note)

        true ? try context.save() : ()

        let notes = try context.fetch(FetchDescriptor<Note>())
        for n in notes {
            print("note: \(n.when) | \(n.title) | \(n.content)")
        }
    }
}
