import Foundation

enum CustomError: Error {
    case invalidArguments
    case invalidURL(String)
    case fileNotFound(String)
}

func appendFilePart(
    to data: inout Data,
    boundary: String,
    fieldName: String,
    filename: String,
    mimeType: String,
    fileData: Data
) {
    data.append("--\(boundary)\r\n".data(using: .utf8)!)
    data.append("Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
    data.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
    data.append(fileData)
    data.append("\r\n".data(using: .utf8)!)
}

func main() throws {
    let args = CommandLine.arguments

    guard args.count == 5 else {
        throw CustomError.invalidArguments
    }

    let endpointString = args[1]
    let metadataPath = args[2]
    let videoPath = args[3]
    let motionDataPath = args[4]

    guard let url = URL(string: endpointString) else {
        throw CustomError.invalidURL(endpointString)
    }

    let fileManager = FileManager.default

    guard fileManager.fileExists(atPath: metadataPath) else {
        throw CustomError.fileNotFound(metadataPath)
    }
    guard fileManager.fileExists(atPath: videoPath) else {
        throw CustomError.fileNotFound(videoPath)
    }
    guard fileManager.fileExists(atPath: motionDataPath) else {
        throw CustomError.fileNotFound(motionDataPath)
    }

    let metadataURL = URL(fileURLWithPath: metadataPath)
    let videoURL = URL(fileURLWithPath: videoPath)
    let motionDataURL = URL(fileURLWithPath: motionDataPath)

    let metadataData = try Data(contentsOf: metadataURL)
    let videoData = try Data(contentsOf: videoURL)
    let motionData = try Data(contentsOf: motionDataURL)

    let boundary = "boundary-\(UUID().uuidString)"
    var body = Data()

    // metadata.json -> field "metadata"
    appendFilePart(
        to: &body,
        boundary: boundary,
        fieldName: "metadata",
        filename: "metadata.json",
        mimeType: "application/json",
        fileData: metadataData
    )

    // video.mov -> field "video"
    appendFilePart(
        to: &body,
        boundary: boundary,
        fieldName: "video",
        filename: "video.mov",
        mimeType: "video/quicktime",
        fileData: videoData
    )

    // motion_data.csv -> field "motion_data"
    appendFilePart(
        to: &body,
        boundary: boundary,
        fieldName: "motion_data",
        filename: "motion_data.csv",
        mimeType: "text/csv",
        fileData: motionData
    )

    body.append("--\(boundary)--\r\n".data(using: .utf8)!)

    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    request.httpBody = body

    let semaphore = DispatchSemaphore(value: 0)

    let task = URLSession.shared.dataTask(with: request) { data, response, error in
        defer { semaphore.signal() }

        if let error = error {
            fputs("request error: \(error)\n", stderr)
            return
        }

        if let httpResponse = response as? HTTPURLResponse {
            print("status: \(httpResponse.statusCode)")
            if !httpResponse.allHeaderFields.isEmpty {
                print("headers:")
                for (key, value) in httpResponse.allHeaderFields {
                    print("  \(key): \(value)")
                }
            }
        }

        if let data = data, !data.isEmpty {
            if let bodyString = String(data: data, encoding: .utf8) {
                print("response body:\n\(bodyString)")
            } else {
                print("response body (binary, \(data.count) bytes)")
            }
        } else {
            print("no response body")
        }
    }

    task.resume()
    semaphore.wait()
}

do {
    try main()
} catch CustomError.invalidArguments {
    let program = (CommandLine.arguments.first as NSString?)?.lastPathComponent ?? "uploader"
    fputs("""
    usage:
      \(program) <endpoint_url> <metadata.json> <video.mov> <motion_data.csv>
    """, stderr)
    exit(1)
} catch CustomError.invalidURL(let url) {
    fputs("invalid URL: \(url)\n", stderr)
    exit(1)
} catch CustomError.fileNotFound(let path) {
    fputs("file not found: \(path)\n", stderr)
    exit(1)
} catch {
    fputs("unexpected error: \(error)\n", stderr)
    exit(1)
}
