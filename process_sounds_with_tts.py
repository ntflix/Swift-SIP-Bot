#!/usr/bin/env python3
"""
Audio processing script that combines TTS (Text-to-Speech) with downloaded audio files.

For each entry in sounds.json, this script:
1. Generates TTS audio for the title
2. Downloads the sound from the provided URL
3. Generates TTS audio for the description
4. Concatenates: title_tts + downloaded_audio + description_tts
5. Converts to SIP-compatible format (16-bit PCM, mono, 8000 Hz)
6. Saves the combined audio to output/{title}.wav
"""

import json
import os
import sys
import hashlib
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import logging

import requests
from pydub import AudioSegment
from gtts import gTTS


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

prepend = "The title of the following recording is, quote, "
append_title = ", end quote. Playback begins now."


class SoundProcessor:
    """Processes sound entries with TTS synthesis."""

    def __init__(
        self,
        sounds_json_path: str,
        tts_speed: float,
        tts_volume: float,
        output_dir: str = "output_sounds",
        cache_dir: str = ".audio_cache",
    ) -> None:
        """
        Initialize the SoundProcessor.

        Args:
            sounds_json_path: Path to the sounds.json file
            output_dir: Directory to save processed audio files
            cache_dir: Directory to cache downloaded audio files
            tts_speed: TTS speech speed (0.8 = slower, 1.0 = normal, higher = faster)
            tts_volume: TTS volume level (0.0 to 1.0) - applied after generation
        """
        self.sounds_json_path = Path(sounds_json_path)
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.tts_speed = tts_speed
        self.tts_volume = tts_volume

        # Create output and cache directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Validate inputs
        if not self.sounds_json_path.exists():
            raise FileNotFoundError(f"sounds.json not found at {self.sounds_json_path}")

    def _text_to_speech(self, text: str, output_path: str) -> bool:
        """
        Convert text to speech and save as WAV file using Google TTS.

        Args:
            text: Text to convert to speech
            output_path: Path to save the generated WAV file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Generating TTS for: {text[:50]}...")

            # Generate MP3 via gTTS (most reliable method)
            tts = gTTS(text=text, lang="en", slow=not (self.tts_speed > 0.9))
            mp3_path = output_path.replace(".wav", ".mp3")
            tts.save(mp3_path)

            # Convert MP3 to WAV using pydub
            audio = AudioSegment.from_mp3(mp3_path)

            # Apply volume adjustment if needed
            if self.tts_volume < 1.0:
                audio = audio - (20 * (1.0 - self.tts_volume))

            audio.export(output_path, format="wav")

            # Clean up temporary MP3
            try:
                os.remove(mp3_path)
            except OSError:
                pass

            return True
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return False

    def _get_cache_path(self, url: str) -> Path:
        """
        Generate a cache path for a given URL.

        Args:
            url: The URL to generate a cache path for

        Returns:
            Path object pointing to the cache file
        """
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}.wav"
        return self.cache_dir / filename

    def _download_audio(self, url: str, output_path: str) -> bool:
        """
        Download audio file from URL with caching support.

        Args:
            url: URL of the audio file
            output_path: Path to save the downloaded file

        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(url)

        # Check if file is already cached
        if cache_path.exists():
            logger.info(f"Using cached audio: {cache_path.name}")
            try:
                with open(cache_path, "rb") as src, open(output_path, "wb") as dst:
                    dst.write(src.read())
                logger.info(f"Copied cached audio to: {output_path}")
                return True
            except OSError as e:
                logger.error(f"Error copying cached audio: {e}")
                return False

        # Download if not cached
        try:
            logger.info(f"Downloading audio from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to both cache and output
            with open(cache_path, "wb") as f:
                f.write(response.content)
            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded and cached to: {cache_path.name}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error downloading audio: {e}")
            return False

    def _combine_audio_files(
        self,
        title_tts_path: str,
        audio_path: str,
        description_tts_path: str,
        output_path: str,
    ) -> bool:
        """
        Combine three audio files in sequence.

        Args:
            title_tts_path: Path to title TTS audio
            audio_path: Path to downloaded audio
            description_tts_path: Path to description TTS audio
            output_path: Path to save combined audio

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Combining audio files...")

            # Load audio files
            title_audio = AudioSegment.from_wav(title_tts_path)
            main_audio = AudioSegment.from_wav(audio_path)
            description_audio = AudioSegment.from_wav(description_tts_path)

            # Concatenate audio files
            combined = title_audio + main_audio + description_audio

            # Export combined audio
            combined.export(output_path, format="wav")
            logger.info(f"Combined audio saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error combining audio files: {e}")
            return False

    def _convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """
        Convert audio to SIP-compatible format using ffmpeg.

        Converts to:
        - 16-bit PCM (Integer)
        - Mono
        - 8000 Hz

        Args:
            input_path: Path to the input WAV file
            output_path: Path to save the converted WAV file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Converting audio format to SIP requirements...")
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-acodec",
                "pcm_s16le",
                "-ac",
                "1",
                "-ar",
                "8000",
                "-y",  # Overwrite output file without asking
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return False

            logger.info(f"Audio converted successfully to: {output_path}")
            return True
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg: brew install ffmpeg")
            return False
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            return False
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename

    def process_sound(self, sound_entry: dict[str, Any]) -> bool:
        """
        Process a single sound entry.

        Args:
            sound_entry: Dictionary containing 'title', 'description', and 'url'

        Returns:
            True if processing was successful, False otherwise
        """
        title: str = sound_entry.get("title", "Unknown")
        description: str = sound_entry.get("description", "No description")
        url: str = sound_entry.get("url", "")

        if not url:
            logger.warning(f"Skipping entry '{title}': No URL provided")
            return False

        # Sanitize filename
        safe_filename = self._sanitize_filename(title)
        output_file = self.output_dir / f"{safe_filename}.wav"

        # Create temporary files
        temp_dir = self.output_dir / ".temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        title_tts_path = temp_dir / f"{safe_filename}_title.wav"
        audio_path = temp_dir / f"{safe_filename}_audio.wav"
        description_tts_path = temp_dir / f"{safe_filename}_description.wav"
        combined_path = temp_dir / f"{safe_filename}_combined.wav"

        try:
            logger.info(f"Processing: {title}")

            # Step 1: Generate TTS for title
            full_title = prepend + title + append_title

            if not self._text_to_speech(full_title, output_path=str(title_tts_path)):
                return False

            # Step 2: Download audio
            if not self._download_audio(url, str(audio_path)):
                return False

            # Step 3: Generate TTS for description
            if not self._text_to_speech(description, str(description_tts_path)):
                return False

            # Step 4: Combine all audio
            if not self._combine_audio_files(
                str(title_tts_path),
                str(audio_path),
                str(description_tts_path),
                str(combined_path),
            ):
                return False

            # Step 5: Convert to SIP-compatible format
            if not self._convert_audio_format(str(combined_path), str(output_file)):
                return False

            logger.info(f"✓ Successfully processed: {title}")
            return True

        except Exception as e:
            logger.error(f"Error processing {title}: {e}")
            return False
        finally:
            # Cleanup temporary files
            for temp_file in [
                title_tts_path,
                audio_path,
                description_tts_path,
                combined_path,
            ]:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass

    def process_all_sounds(self) -> None:
        """Process all sounds in the JSON file."""
        try:
            with open(self.sounds_json_path, "r", encoding="utf-8") as f:
                sounds: list[dict[str, Any]] = json.load(f)

            total = len(sounds)
            successful = 0

            logger.info(f"Starting to process {total} sound entries...")

            for index, sound_entry in enumerate(sounds, 1):
                logger.info(f"Processing {index}/{total}...")
                if self.process_sound(sound_entry):
                    successful += 1

            logger.info(f"\n{'='*60}")
            logger.info(f"Processing complete!")
            logger.info(f"Successfully processed: {successful}/{total}")
            logger.info(f"Output saved to: {self.output_dir.absolute()}")
            logger.info(f"{'='*60}")

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)


def main() -> None:
    """Main entry point."""
    # Configuration
    sounds_json = "sounds.json"
    output_directory = "sounds"

    # Initialize processor
    processor = SoundProcessor(
        sounds_json_path=sounds_json,
        tts_speed=1.1,  # 0.8 = slower, 1.0 = normal (gTTS uses slow=True for this)
        tts_volume=1.0,  # Adjust volume (0.0-1.0)
        output_dir=output_directory,
    )

    # Process all sounds
    processor.process_all_sounds()


if __name__ == "__main__":
    main()
