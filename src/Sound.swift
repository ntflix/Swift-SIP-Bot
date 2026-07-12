import Foundation

struct Sound {
    static var audioFilesDirectory: String = "sounds"

    static func audioFiles(directory: String? = nil) -> [URL] {
        let dirPath = directory ?? audioFilesDirectory
        let soundsDirectory = URL(fileURLWithPath: dirPath)

        do {
            let fileManager = FileManager.default
            let files = try fileManager.contentsOfDirectory(
                at: soundsDirectory, includingPropertiesForKeys: nil)

            // Filter for common audio file formats
            let audioExtensions = ["wav", "mp3", "m4a", "aac", "flac", "ogg"]
            let audioFiles = files.filter { url in
                audioExtensions.contains(url.pathExtension.lowercased())
            }

            if audioFiles.isEmpty {
                print("No audio files found in sounds directory: \(soundsDirectory.path)")
            } else {
                print("Found \(audioFiles.count) audio file(s) in sounds directory")
            }

            return audioFiles
        } catch {
            print("Error reading sounds directory: \(error)")
            return []
        }
    }
}
