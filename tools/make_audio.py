"""Синтезделген дыбыстарды assets/audio/*.wav файлдарына жазады (браузер нұсқасы үшін жылдам жүктеу).

Іске қосу: python tools/make_audio.py [шығыс_папка]
"""
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kolenke.core.audio_synth import RATE, SOUNDS


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    for name, make in SOUNDS.items():
        with wave.open(str(out / f"{name}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(make())
    print("wav:", len(SOUNDS), "->", out)


if __name__ == "__main__":
    main()
