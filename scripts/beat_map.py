#!/usr/bin/env python3
"""Analyze an audio file for beat or onset candidates."""
import argparse
import json
from pathlib import Path


def track_beats(audio):
    import librosa

    waveform, rate = librosa.load(audio, sr=22050, mono=True)
    hop = 256
    envelope = librosa.onset.onset_strength(y=waveform, sr=rate, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=envelope, sr=rate, hop_length=hop, units="time")
    onsets = librosa.onset.onset_detect(onset_envelope=envelope, sr=rate, hop_length=hop, units="time")
    return f"librosa {librosa.__version__}", len(waveform) / rate, float(tempo.item()), beats, onsets


def find_wav_onsets(audio):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import find_peaks

    rate, waveform = wavfile.read(audio)
    window = max(1, rate // 100)
    total = len(waveform) // window * window
    blocks = waveform[:total].reshape(-1, window, *waveform.shape[1:]).astype(np.float64)
    if not len(blocks):
        raise SystemExit("音频太短，无法提取音头。")
    rms = np.sqrt(np.mean(blocks ** 2, axis=tuple(range(1, blocks.ndim))))
    rise = np.diff(rms, prepend=0)
    peaks = find_peaks(rise, height=max(float(rise.max()) * 0.25, 1e-12), distance=10)[0]
    return "SciPy RMS onset candidates", len(waveform) / rate, None, [], peaks * window / rate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--onsets-only", action="store_true", help="Use SciPy to estimate WAV onsets without inferring beats")
    args = parser.parse_args()
    analyze = find_wav_onsets if args.onsets_only else track_beats
    analyzer, duration, tempo, beats, onsets = analyze(args.audio)
    if not len(beats) and not len(onsets):
        raise SystemExit("没有检测出可靠的候选点；请试听并标注时间。")
    payload = {
        "source": args.audio.name,
        "analyzer": analyzer,
        "duration_s": round(duration, 4),
        "tempo_bpm": round(tempo, 2) if tempo else None,
        "beats_s": [round(float(t), 4) for t in beats],
        "onsets_s": [round(float(t), 4) for t in onsets],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(beats)} 个拍点，{len(onsets)} 个候选音头 → {args.output}")


if __name__ == "__main__":
    main()
