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
            configurations: ModelConfiguration(url: URL(fileURLWithPath: "./async-cli.store"))
        )

        let context = container.mainContext
        let note = Note(title: "aloha!", content: "swift-data in cli")
        context.insert(note)

        false ? try context.save() : ()

        let notes = try context.fetch(FetchDescriptor<Note>())
        for n in notes {
            print("note: \(n.when) | \(n.title) | \(n.content)")
        }

        let back = Task.detached {
            let delay = 4 + Double.random(in: 0 ... 1)
            print("background task started, sleep for \(delay) seconds...")
            try await Task.sleep(for: .seconds(Int(delay)))
            print("background task finished")
            return 100
        }
        let clock = ContinuousClock()
        let elapsed = try await clock.measure {
            let x = try await withThrowingTaskGroup(of: FetchResult.self, returning: Int.self) { group in
                for n in 1 ... 5 {
                    group.addTask {
                        try await self.fetch(task: n)
                    }
                    print(n)
                }
                var results: [FetchResult] = []
                defer { print(results) }

                for try await group in group {
                    results.append(group)
                }
                return results.count
            }
            print("N = \(x)")
            back.cancel()
        }
        print(elapsed)
        do {
            print("background:", try await back.value)
        } catch {
            print("background has been cancelled:", await back.result)
        }
    }

    static func fetch(task n: Int) async throws -> FetchResult {
        let request = URL(string: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv")!
        var i = 0
        for try await event in request.lines.dropFirst() {
            let values = event.split(separator: ",")
            false ? print("\(n) | \(i) | \(values)") : ()
            i += 1
        }
        let delay = Double.random(in: 0 ... 1)
        try await Task.sleep(for: .seconds(delay))
        print("task \(n), delay \(delay), done")
        return (task: n, N: i)
    }
}
