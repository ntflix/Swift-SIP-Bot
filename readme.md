# Sounds From Beyond (SIP Bot)

1. Receives SIP call
2. Picks up
3. Plays a randomly selected sound from NASA's Sounds From Beyond collection
4. Speaks details of the sound
5. Hangs up

## Entries

Entries are stored in `sounds.json` with the following schema:

```json
[
  {
    "title": "First Audio Recording of Sounds on Mars",
    "description": "This recording was made by the SuperCam instrument on NASA’s Perseverance Mars rover on Feb. 19, 2021, just about 18 hours after landing on the mission’s first sol or Martian day. The rover’s mast, holding the microphone, was still stowed on Perseverance’s deck, and so the sound is muffled, a little like the sound one hears listening to a seashell or having a hand cupped over the ear. Just a little wind can be heard. Credit: NASA/JPL-Caltech/LANL/CNES/CNRS/ISAE-Supaero",
    "url": "https://www.nasa.gov/wp-content/uploads/2024/05/scam-mic-sol001-run001.wav"
  }
]
```

## Running

When started, the program checks whether all the sounds in `sounds.json` have been downloaded to the `sounds` directory.

Filenames are synthesised from the path component of the URL, so the above entry would be saved as `sounds/scam-mic-sol001-run001.wav`.

### Command-line Arguments

- `--creds <path>`: Path to a JSON file containing SIP credentials (default: `creds.json`)
- `--audio-files-dir <path>`: Directory containing audio files to randomly select from (default: `sounds`)

The credentials file must contain the following fields:

```json
{
  "SIP_USERNAME": "your-sip-username",
  "SIP_PASSWORD": "your-sip-password",
  "SIP_SERVER": "your-sip-server"
}
```

Example usage:

```bash
./MyBaresipApp --creds creds.json --audio-files-dir sounds
```

### Environment Variables

To give callers time to put the phone to their ear before the first sound starts, set `CALL_ANSWER_DELAY_SECONDS` to a non-negative number of seconds. For example, `CALL_ANSWER_DELAY_SECONDS=2.5` adds a 2.5 second delay before each incoming call is answered.

## Audio files

`aufile` does not use standard macOS `AVFoundation` to parse the file; it manually reads the RIFF headers. If the `.wav` file has any extension chunks, floating-point data, or an unsupported sample rate/bit-depth, the parser aborts with `ENOSYS` ("Function not implemented").

It must be converted to:

- 16-bit PCM (Integer)
- Mono
- 8000 Hz

`ffmpeg -i input.wav -acodec pcm_s16le -ac 1 -ar 8000 output.wav`
