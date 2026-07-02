"""Command-line voice interface for JARVIS."""

import argparse
import asyncio

from core import initialize_jarvis
from speech import MicrophoneManager, SpeechPipeline, WakeWordListener


def list_microphones() -> None:
    manager = MicrophoneManager()
    devices = manager.list_input_devices(include_loopback=False)
    default = manager.get_default_input_device()
    default_index = default.index if default else None
    for device in devices:
        marker = " (default)" if device.index == default_index else ""
        print(
            f"[{device.index}] {device.name}"
            f" | channels={device.channels}"
            f" | rate={device.default_sample_rate}{marker}"
        )


async def listen_once(args) -> None:
    jarvis = initialize_jarvis(args.config)
    pipeline = SpeechPipeline(
        jarvis,
        whisper_model=args.whisper_model,
        tts_rate=jarvis.config.get("jarvis.voice.rate", 150),
        tts_volume=jarvis.config.get("jarvis.voice.volume", 0.8),
    )
    response = await pipeline.listen_process_respond(
        device_index=args.device_index,
        preferred_device_name=args.device_name,
        speak_response=not args.no_speak,
        timeout=args.timeout,
        phrase_time_limit=args.phrase_time_limit,
    )
    print(response)


async def listen_wake(args) -> None:
    jarvis = initialize_jarvis(args.config)
    pipeline = SpeechPipeline(
        jarvis,
        whisper_model=args.whisper_model,
        tts_rate=jarvis.config.get("jarvis.voice.rate", 150),
        tts_volume=jarvis.config.get("jarvis.voice.volume", 0.8),
    )
    wake_words = [word.strip() for word in args.wake_word.split(",") if word.strip()]
    listener = WakeWordListener(
        pipeline,
        wake_words=wake_words,
        poll_delay=args.poll_delay,
    )
    print(f"Listening for wake word: {', '.join(wake_words)}")
    stats = await listener.run(
        device_index=args.device_index,
        preferred_device_name=args.device_name,
        speak_response=not args.no_speak,
        timeout=args.timeout,
        phrase_time_limit=args.phrase_time_limit,
        max_cycles=args.max_cycles,
    )
    print(stats)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JARVIS voice assistant CLI")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-mics", help="List active physical input devices")

    listen = subparsers.add_parser("listen-once", help="Listen once, process, and speak the response")
    listen.add_argument("--device-index", type=int, default=None, help="PyAudio input device index")
    listen.add_argument("--device-name", default=None, help="Substring of microphone name to prefer")
    listen.add_argument("--whisper-model", default="base", help="Whisper model name")
    listen.add_argument("--timeout", type=float, default=5, help="Seconds to wait for speech")
    listen.add_argument("--phrase-time-limit", type=float, default=8, help="Max seconds to record")
    listen.add_argument("--no-speak", action="store_true", help="Do not speak the response")

    wake = subparsers.add_parser("listen-wake", help="Continuously listen for the wake word")
    wake.add_argument("--device-index", type=int, default=None, help="PyAudio input device index")
    wake.add_argument("--device-name", default=None, help="Substring of microphone name to prefer")
    wake.add_argument("--whisper-model", default="base", help="Whisper model name")
    wake.add_argument("--wake-word", default="jarvis", help="Wake word or comma-separated wake words")
    wake.add_argument("--timeout", type=float, default=4, help="Seconds to wait for each phrase")
    wake.add_argument("--phrase-time-limit", type=float, default=6, help="Max seconds per phrase")
    wake.add_argument("--poll-delay", type=float, default=0.2, help="Delay between loop iterations")
    wake.add_argument("--max-cycles", type=int, default=None, help="Optional test/debug loop limit")
    wake.add_argument("--no-speak", action="store_true", help="Do not speak responses")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "list-mics":
        list_microphones()
    elif args.command == "listen-once":
        asyncio.run(listen_once(args))
    elif args.command == "listen-wake":
        asyncio.run(listen_wake(args))


if __name__ == "__main__":
    main()
