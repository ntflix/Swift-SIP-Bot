import CBaresip

func randomiseAudioSource(directory: String? = nil) {
    let audioFiles = Sound.audioFiles(directory: directory)
    guard !audioFiles.isEmpty else {
        print("No audio files available to randomize.")
        return
    }

    let randomIndex = Int.random(in: 0..<audioFiles.count)
    let selectedAudioFile = audioFiles[randomIndex]

    print("Randomly selected audio file: \(selectedAudioFile)")

    let configPtr = conf_config()

    setupAudioSource(
        cfg: configPtr, wavPath: selectedAudioFile.path)

}
