import Foundation

typealias FetchResult = (task: Int, N: Int)

@main
struct cli {
    static func main() async throws {
        let back = Task.detached {
            let delay = 4 + Double.random(in: 0...1)
            print("background task started, sleep for \(delay) seconds...")
            try await Task.sleep(for: .seconds(Int(delay)))
            print("background task finished")
            return 100
        }
        let clock = ContinuousClock()
        let elapsed = try await clock.measure {
            let x = try await withThrowingTaskGroup(of: FetchResult.self, returning: Int.self) {
                group in
                for n in 1...5 {
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

    static let url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv"

    static func fetch(task n: Int) async throws -> FetchResult {
        let request = URL(
            string: url)!
        var i = 0
        for try await event in request.lines.dropFirst() {
            let values = event.split(separator: ",")
            false ? print("\(n) | \(i) | \(values)") : ()
            i += 1
        }
        let delay = Double.random(in: 0...1)
        try await Task.sleep(for: .seconds(delay))
        print("task \(n), delay \(delay), done")
        return (task: n, N: i)
    }
}
