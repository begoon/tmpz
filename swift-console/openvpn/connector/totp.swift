import CryptoKit
import Foundation

func totp(using secret: String) -> String {
    let period = TimeInterval(30)
    let digits = 6
    var counter = UInt64(Date().timeIntervalSince1970 / period).bigEndian

    guard let secretData = try? Base32.decode(string: secret) else {
        return "?"
    }

    let counterData = withUnsafeBytes(of: &counter) { Array($0) }
    let hash = HMAC<Insecure.SHA1>.authenticationCode(
        for: counterData,
        using: SymmetricKey(data: secretData)
    )

    var truncatedHash = hash.withUnsafeBytes { ptr -> UInt32 in
        let offset = ptr[hash.byteCount - 1] & 0x0f

        let truncatedHashPtr = ptr.baseAddress! + Int(offset)
        return truncatedHashPtr.bindMemory(to: UInt32.self, capacity: 1).pointee
    }

    truncatedHash = UInt32(bigEndian: truncatedHash)
    truncatedHash = truncatedHash & 0x7FFF_FFFF
    truncatedHash = truncatedHash % UInt32(pow(10, Float(digits)))

    return "\(String(format: "%0*u", digits, truncatedHash))"
}
