import Alamofire
import Foundation

let url = URL(string: "https://api.ipify.org?format=json")!

print("BEFORE")

try await print("Alamofire:", AF.request(url).serializingString().value)
try await print("URLSession:", String(data: URLSession.shared.data(from: url).0, encoding: .utf8)!)

print("AFTER")
