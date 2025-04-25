import Foundation

func fetcher(_ n: Int) async throws {
    let request = URL(string: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv")!
    for try await event in request.lines.dropFirst() {
        let values = event.split(separator: ",")
        print("\(n) | \(values)")
    }
}

let clock = ContinuousClock()
let elapsed = try await clock.measure {
    try await withThrowingTaskGroup(of: Int.self) { group in
        for n in 1 ... 5 {
            group.addTask {
                try await fetcher(n)
                return n
            }
        }
        var results: [Int] = []
        for try await group in group {
            results.append(group)
        }
        print(results)
    }
}

print(elapsed)
