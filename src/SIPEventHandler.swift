import CBaresip
import Dispatch
import Foundation

// Note the signature: (bevent_ev, OpaquePointer?, UnsafeMutableRawPointer?)
public func sipEventHandler(
    event: bevent_ev,
    beventPtr: OpaquePointer?,
    arg: UnsafeMutableRawPointer?
) {
    // 1. Get the event string using baresip's C helper
    if let cString = bevent_str(event) {
        let eventName = String(cString: cString)
        print("Received Baresip Event: \(eventName)")
    }

    // 2. Direct comparison (no .rawValue needed because it's a true enum in Swift)
    if event == BEVENT_CALL_INCOMING {
        print("Incoming call detected!")
        randomiseAudioSource(directory: Sound.audioFilesDirectory)

        // 3. Extract the 'struct call *' safely using the C getter
        let callPtr = bevent_get_call(beventPtr)

        if let validCall = callPtr {
            let delaySeconds = IncomingCallTiming.answerDelaySeconds
            let callAddress = UInt(bitPattern: validCall)

            @Sendable
            func answerIncomingCall() {
                guard let call = OpaquePointer(bitPattern: callAddress) else {
                    print("Failed to answer call: invalid pointer address.")
                    return
                }

                print("Auto-answering incoming call...")
                let err = call_answer(call, 200, VIDMODE_OFF)
                if err != 0 {
                    print("Failed to answer call, error: \(err)")
                }
            }

            if delaySeconds > 0 {
                print("Delaying incoming call answer by \(delaySeconds) seconds.")
                let delayMilliseconds = Int((delaySeconds * 1000).rounded())
                DispatchQueue.global().asyncAfter(
                    deadline: .now() + .milliseconds(delayMilliseconds)
                ) {
                    answerIncomingCall()
                }
            } else {
                answerIncomingCall()
            }
        }
    } else if event == BEVENT_CALL_CLOSED {
        print("Call ended or connection reset.")
    }
}
