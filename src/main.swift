// The Swift Programming Language
// https://docs.swift.org/swift-book

import CBaresip
import Foundation

func configuredIncomingCallAnswerDelaySeconds() -> TimeInterval {
    let key = "CALL_ANSWER_DELAY_SECONDS"
    guard let rawValue = ProcessInfo.processInfo.environment[key], !rawValue.isEmpty else {
        return 0
    }

    guard let delay = TimeInterval(rawValue), delay >= 0 else {
        print("Ignoring invalid \(key) value '\(rawValue)'; using 0 seconds.")
        return 0
    }

    return delay
}

struct Credentials: Decodable {
    let SIP_USERNAME: String
    let SIP_PASSWORD: String
    let SIP_SERVER: String
}

struct SoundsFromBeyond {
    private let sipUsername: String
    private let sipPassword: String
    private let sipServer: String
    private let sipPort = "5060"
    private let audioFilesDir: String

    // We need to keep a reference to the agent pointer
    private var agent: OpaquePointer? = nil

    init(credentials: Credentials, audioFilesDir: String = "sounds") {
        self.sipUsername = credentials.SIP_USERNAME
        self.sipPassword = credentials.SIP_PASSWORD
        self.sipServer = credentials.SIP_SERVER
        self.audioFilesDir = audioFilesDir
    }

    mutating func start() async throws {
        print("Starting SIP...")

        // Format: sip:username:password@server
        let sipAddr =
            "<sip:\(sipUsername)@\(sipServer):\(sipPort)>;auth_pass=\(sipPassword)"

        print("Registering with: \(sipAddr)")

        var error = libre_init()
        guard error == 0 else {
            print("Failed to initialize libre: \(error)")
            return
        }

        error = conf_configure()
        guard error == 0 else {
            print("Failed to configure baresip: \(error)")
            return
        }

        randomiseAudioSource()

        error = baresip_init(conf_config())
        guard error == 0 else {
            print("Failed to initialize baresip: \(error)")
            return
        }

        // ua_init(software, udp, tcp, tls)
        error = ua_init("SoundsFromBeyond Swift Bot", true, false, false)
        guard error == 0 else {
            print("Failed to init User Agent subsystem: \(error)")
            return
        }

        // Load dynamic modules
        error = conf_modules()
        guard error == 0 else {
            print("Failed to load modules: \(error)")
            return
        }

        // Disable all host audio interaction modules
        // Unload any modules that interact with the host's audio devices
        let modulesToDisable = [
            "stdio", "cons", "account", "alsa", "osxaudio", "portaudio", "pulse", "audiounit",
            "coreaudio",
        ]

        for mod in modulesToDisable {
            mod.withCString { cModName in
                // Unload the module if it exists
                module_unload(cModName)
            }
        }

        // Only load the aufile module for serving audio files
        let modulesToLoad = ["aufile"]
        let homebrewModPath = "/opt/homebrew/lib/baresip/modules"
        for mod in modulesToLoad {
            mod.withCString { cModName in
                // Load the module if it's not already loaded
                if module_load(homebrewModPath, cModName) != 0 {
                    print("Failed to load module: \(mod)")
                }
            }
        }

        print("Registering with: \(sipAddr)")

        // Set the audio files directory for the event handler to use
        Sound.audioFilesDirectory = audioFilesDir

        // bevent_register expects (handler, arg)
        let err = bevent_register(sipEventHandler, nil)
        if err != 0 {
            print("Failed to register event handler: \(err)")
        }

        // Allocate the user agent ON THIS THREAD
        sipAddr.withCString { cString in
            error = ua_alloc(&self.agent, cString)
        }

        guard error == 0, let validAgent = self.agent else {
            print("Failed to allocate user agent: \(error)")
            throw SIPStartupError.failedToAllocateUserAgent
        }

        let account = ua_account(validAgent)
        account_set_regint(account, 69)

        if let aorCStr = account_aor(account) {
            print("Account AOR: \(String(cString: aorCStr))")
        }

        // Baresip requires rebuilding the registration clients internally when the account changes.
        // Calling ua_update_account applies the new regint setting.
        error = ua_update_account(validAgent)
        if error != 0 {
            print("Failed to update account: \(error)")
        }

        print("Bot initialized and attempting registration...")
        error = ua_register(validAgent)
        if error != 0 {
            print("Warning: ua_register returned \(error). Registration may have failed.")
        } else {
            print("Registration initiated successfully.")
        }

        // Run the event loop ON THIS THREAD
        re_main(nil)

        // When re_main ends, cleanup
        self.cleanup()
    }

    private mutating func cleanup() {
        if let agentPtr = agent {
            // Memory dereference is part of libre's reference counting system
            mem_deref(UnsafeMutableRawPointer(agentPtr))
        }
        ua_close()
        bevent_unregister(sipEventHandler)
        mod_close()
        baresip_close()
        libre_close()
    }
}

IncomingCallTiming.answerDelaySeconds = configuredIncomingCallAnswerDelaySeconds()
if IncomingCallTiming.answerDelaySeconds > 0 {
    print("Incoming calls will be answered after \(IncomingCallTiming.answerDelaySeconds) seconds.")
}

// Parse command-line arguments
var credsPath = "creds.json"
var audioFilesDir = "sounds"
let arguments = CommandLine.arguments
var i = 1
while i < arguments.count {
    if arguments[i] == "--creds" && i + 1 < arguments.count {
        credsPath = arguments[i + 1]
        i += 2
    } else if arguments[i] == "--audio-files-dir" && i + 1 < arguments.count {
        audioFilesDir = arguments[i + 1]
        i += 2
    } else {
        i += 1
    }
}

// Load credentials from JSON file
let credsFileURL = URL(fileURLWithPath: credsPath)
guard FileManager.default.fileExists(atPath: credsPath) else {
    print("Error: Credentials file not found at \(credsPath)")
    exit(1)
}

let credsData: Data
do {
    credsData = try Data(contentsOf: credsFileURL)
} catch {
    print("Error: Failed to read credentials file at \(credsPath): \(error)")
    exit(1)
}

let credentials: Credentials
do {
    credentials = try JSONDecoder().decode(Credentials.self, from: credsData)
} catch {
    print("Error: Failed to parse credentials JSON: \(error)")
    exit(1)
}

// Instantiate and run asynchronously to avoid blocking the main thread with re_main's loop. We use dispatchMain() to keep the program running indefinitely until interrupted
var bot = SoundsFromBeyond(credentials: credentials, audioFilesDir: audioFilesDir)
Task {
    try await bot.start()
}
dispatchMain()
