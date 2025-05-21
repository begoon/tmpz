import Foundation

let greeting = "Ha?"
print(type(of: greeting), Thread.current)

actor Counter {
    var x: Int = 0

    func increment() {
        x += 1
        print("$", x, terminator: " -> ")
    }
}

var counter = Counter()
print(CFGetRetainCount(counter))

Task {
    for i in 0 ..< 10 {
        print("@", i, await Task.detached {
            await counter.increment()
        }.value)
    }
    await print("x", counter.x)
}
