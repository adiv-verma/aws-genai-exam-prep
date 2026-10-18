import Foundation
import Vision
import AppKit

// Usage: ocr <image.png> ...   — prints recognized lines, one per line, in reading order.
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        FileHandle.standardError.write("cannot load \(path)\n".data(using: .utf8)!)
        continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    req.recognitionLanguages = ["en-US"]
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    try? handler.perform([req])
    guard let obs = req.results else { continue }

    // sort top-to-bottom, then left-to-right (Vision origin is bottom-left)
    let sorted = obs.sorted { a, b in
        let ay = a.boundingBox.midY, by = b.boundingBox.midY
        if abs(ay - by) > 0.006 { return ay > by }
        return a.boundingBox.minX < b.boundingBox.minX
    }
    for o in sorted {
        if let t = o.topCandidates(1).first { print(t.string) }
    }
}
