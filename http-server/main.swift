// swift-tools-version:5.2
import Foundation
import NIO
import NIOHTTP1

struct Version: Codable {
    let version: String
}

func jsonResponse<T: Codable>(_ value: T) -> Data {
    let encoder = JSONEncoder()
    encoder.outputFormatting = .prettyPrinted
    return (try? encoder.encode(value)) ?? Data()
}

final class HTTPHandler: ChannelInboundHandler {
    typealias InboundIn = HTTPServerRequestPart
    typealias OutboundOut = HTTPServerResponsePart
    
    func channelRead(context: ChannelHandlerContext, data: NIOAny) {
        let req = self.unwrapInboundIn(data)
        
        switch req {
        case .head(let requestHead):
            if requestHead.uri == "/version" && requestHead.method == .GET {
                let version = Version(version: "1.0")
                let response = jsonResponse(version)
                
                var headers = HTTPHeaders()
                headers.add(name: "Content-Type", value: "application/json")
                headers.add(name: "Content-Length", value: "\(response.count)")
                
                let responseHead = HTTPResponseHead(version: requestHead.version,
                                                    status: .ok,
                                                    headers: headers)
                context.write(self.wrapOutboundOut(.head(responseHead)), promise: nil)
                var buffer = context.channel.allocator.buffer(capacity: response.count)
                buffer.writeBytes(response)
                context.write(self.wrapOutboundOut(.body(.byteBuffer(buffer))), promise: nil)
                context.writeAndFlush(self.wrapOutboundOut(.end(nil)), promise: nil)
            } else {
                let responseHead = HTTPResponseHead(version: requestHead.version, status: .notFound)
                context.write(self.wrapOutboundOut(.head(responseHead)), promise: nil)
                context.writeAndFlush(self.wrapOutboundOut(.end(nil)), promise: nil)
            }
            
        case .body:
            break
            
        case .end:
            break
        }
    }
}

let group = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
let bootstrap = ServerBootstrap(group: group)
    .childChannelInitializer { channel in
        channel.pipeline.configureHTTPServerPipeline().flatMap {
            channel.pipeline.addHandler(HTTPHandler())
        }
    }

defer {
    try? group.syncShutdownGracefully()
}

let serverChannel = try bootstrap.bind(host: "127.0.0.1", port: 8000).wait()
print("listening on http://127.0.0.1:8000")
try serverChannel.closeFuture.wait()
