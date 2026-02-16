# Test Fixtures

This directory contains audio files for testing the Clarity analysis pipeline.

## Files

### `sample.webm`
- **Source:** Android Recorder app
- **Purpose:** Primary test fixture for Epic 0.2 (Audio Ingestion Pipeline)
- **Format:** WebM container with Opus/Vorbis audio codec (to be verified with ffprobe in ticket 0.2.2)
- **Size:** ~72 KB
- **Usage:** Used for testing audio loading, conversion, and transcription

## Future Fixtures Needed (per ticket 0.1.3)

- **Calibration fixture:** A second `.webm` file with known word count for WPM calibration testing
- **Edge cases:** Corrupt file, empty file, unsupported codec

## Notes

- Fixtures are version-controlled (see `.gitignore` exception for `tests/fixtures/*.webm`)
- ffmpeg metadata will be documented once ffmpeg is installed (Epic 0.2)
