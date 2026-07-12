import CBaresip
import Foundation

func setupAudioSource(cfg: UnsafeMutablePointer<config>?, wavPath: String) {
    // Disable host audio interaction completely
    // Set audio_path to empty to prevent recording/playback to host devices
    "".withCString { cPath in
        str_ncpy(&cfg!.pointee.audio.audio_path.0, cPath, 256)
    }

    // Use aufile module for audio source (only file playback, no microphone)
    str_ncpy(&cfg!.pointee.audio.src_mod.0, "aufile", 256)
    str_ncpy(&cfg!.pointee.audio.src_dev.0, wavPath, 256)

    // Disable playback to host speakers by not setting a playback module
    // This ensures audio only goes over SIP, not to the host's speakers
    "".withCString { cPath in
        str_ncpy(&cfg!.pointee.audio.play_mod.0, cPath, 256)
    }
    "".withCString { cPath in
        str_ncpy(&cfg!.pointee.audio.play_dev.0, cPath, 256)
    }

    // Allow multiple concurrent calls and do not automatically hold other calls.
    // 0 = unlimited calls according to baresip config semantics.
    cfg!.pointee.call.max_calls = 0
    cfg!.pointee.call.hold_other_calls = false
}
