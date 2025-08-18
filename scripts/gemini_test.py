#!/usr/bin/env python3
import os
import sys
import argparse
import textwrap
import time
import base64
import io
from typing import List, Tuple

import requests
import soundfile as sf

MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.5-pro-002",
    "gemini-2.0-flash-exp",
]


def safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return None


def strip_code_fences(s: str) -> str:
    t = s.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.lower().startswith("json\n"):
            t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def flac_b64_from_audio(audio_path: str) -> str:
    data, sr = sf.read(audio_path, dtype="float32", always_2d=True)
    y = data.mean(axis=1)
    buf = io.BytesIO()
    sf.write(buf, y, sr, format="FLAC")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def chunk_audio_to_flac_b64(audio_path: str, chunk_seconds: int) -> List[Tuple[str, float]]:
    data, sr = sf.read(audio_path, dtype="float32", always_2d=True)
    y = data.mean(axis=1)
    samples_per_chunk = max(1, int(sr * chunk_seconds))
    total = len(y)
    chunks: List[Tuple[str, float]] = []
    start = 0
    while start < total:
        end = min(total, start + samples_per_chunk)
        buf = io.BytesIO()
        sf.write(buf, y[start:end], sr, format="FLAC")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        chunks.append((b64, float(start) / float(sr)))
        start = end
    return chunks


def call_gemini_text(api_key: str, model: str, prompt: str, timeout: int = 30) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, params={"key": api_key}, json=payload, timeout=timeout)
    return {"status": r.status_code, "text": r.text, "json": safe_json(r)}


def call_gemini_audio_b64(api_key: str, model: str, b64: str, prompt: str, timeout: int = 60) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "audio/flac", "data": b64}},
                {"text": prompt},
            ]
        }]
    }
    r = requests.post(url, params={"key": api_key}, json=payload, timeout=timeout)
    return {"status": r.status_code, "text": r.text, "json": safe_json(r)}


def is_unavailable(res: dict) -> bool:
    if res.get("status") == 503:
        return True
    data = res.get("json")
    try:
        if data and isinstance(data, dict):
            err = data.get("error") or {}
            status = err.get("status")
            if status == "UNAVAILABLE":
                return True
    except Exception:
        pass
    return False


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Test Gemini on text or audio; stitches chunked audio results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            f"""
            Examples:
              GEMINI_API_KEY=... python scripts/gemini_test.py -m {MODELS[0]} -t "Hello world lyrics"
              GEMINI_API_KEY=... python scripts/gemini_test.py -m {MODELS[0]} --audio ~/Desktop/"Come as you are.wav" --chunk-seconds 60 --sleep-between 15

            Models:\n              - """ + "\n              - ".join(MODELS)
        ),
    )
    p.add_argument("-m", "--model", default=MODELS[0], choices=MODELS, help="Gemini model to use")
    p.add_argument("-t", "--text", default="Hello world", help="Transcript text (used when --audio not given)")
    p.add_argument("--audio", help="Path to audio file (sent as FLAC inline data)")
    p.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds")
    p.add_argument("--chunk-seconds", type=int, default=60, help="Audio chunk size in seconds")
    p.add_argument("--sleep-between", type=int, default=15, help="Seconds to sleep between chunk calls")
    args = p.parse_args(argv)

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        return 2

    if args.audio:
        parts = chunk_audio_to_flac_b64(args.audio, args.chunk_seconds)
        rows: List[Tuple[float, float, str, str]] = []  # start, end, lyric, chord
        backoffs = [60, 300]  # 1 minute, then 5 minutes
        unavailable_hits = 0
        for idx, (b64, start_s) in enumerate(parts, start=1):
#            prompt = (
#                f"This is chunk {idx}/{len(parts)} of the song. Analyze only this chunk.\n"
#                "1) Transcribe the lead vocal and rewrite as improved lyrics.\n"
#                "2) For each word, infer the harmonic chord WITH QUALITY using standard chord symbols and details.\n"
#                "   Examples: C, Am, D7, Gmaj7/B, Fsus4, Eadd9, Bdim, Aaug, Em9, C#7b9, F#maj7#11.\n"
#                "3) Also extract a simple melody as notes with midi pitch and times (optional).\n"
#                "Return STRICT JSON with keys 'words', 'chords', 'notes'.\n"
#                "- words: array of objects with key 'text'.\n"
#                "- chords: array of objects with keys: 'symbol' (full chord symbol string), 'root' (e.g., C, F#, Bb),\n"
#                "          'quality' (e.g., maj, min, 7, maj7, min7, dim, aug, sus2, sus4, add9, 9, 11, 13, b9, #11, b13),\n"
#                "          and optional 'bass' (slash bass like E or Bb if inversion, else null).\n"
#                "- notes: array of objects with keys 'pitch_midi', 'start_sec', 'end_sec'.\n"
#                "- Ensure words and chords arrays are the same LENGTH and index-aligned.\n"
#                "- Do NOT include code fences or prose, only JSON.\n"
#            )
            prompt = (
                f"This is chunk {idx}/{len(parts)} of the song. Analyze only this chunk.\n"
                "1) Transcribe the lead vocal and rewrite as improved lyrics.\n"
                "2) For each word, infer the harmonic chord WITH QUALITY using standard chord symbols and details.\n"
                "   Examples: C, Am, D7, Gmaj7/B, Fsus4, Eadd9, Bdim, Aaug, Em9, C#7b9, F#maj7#11.\n"
                "3) Also extract a simple melody as notes with midi pitch and times (optional).\n"
                "Return STRICT JSON with keys 'words', 'chords', 'notes'.\n"
                "- words: array of objects with keys 'text', 'start_sec', 'end_sec'.\n"
                "- chords: array of objects with keys: 'symbol' (full chord symbol string), 'root' (e.g., C, F#, Bb),\n"
                "  'quality' (e.g., maj, min, 7, maj7, min7, dim, aug, sus2, sus4, add9, 9, 11, 13, b9, #11, b13),\n"
                "  and optional 'bass' (slash bass like E or Bb if inversion, else null).\n"
                "- notes: array of objects with keys 'pitch_midi', 'start_sec', 'end_sec' (optional).\n"
                "- Ensure words and chords arrays are the same LENGTH and index-aligned.\n"
                "- Do NOT include code fences or prose, only JSON.\n"
            )

            # Call with controlled backoff on UNAVAILABLE
            while True:
                res = call_gemini_audio_b64(api_key, args.model, b64, prompt, timeout=max(args.timeout, 60))
                if not is_unavailable(res):
                    break
                if unavailable_hits >= len(backoffs):
                    print("Aborting: service UNAVAILABLE after multiple backoffs")
                    return 1
                delay = backoffs[unavailable_hits]
                unavailable_hits += 1
                print(f"Service UNAVAILABLE; backing off for {delay} seconds...")
                time.sleep(delay)
            print(f"Chunk {idx}/{len(parts)} -> HTTP {res['status']}")
            head = (res["text"] or "")[:400]
            print("Response head:\n" + head)
            if res["json"] is not None:
                try:
                    cand = res["json"]["candidates"][0]["content"]["parts"][0]["text"]
                    text = strip_code_fences(cand)
                    import json as _json
                    obj = _json.loads(text)
                    words_list = obj.get("words", [])
                    chords_list = obj.get("chords", [])
                    m = min(len(words_list), len(chords_list))
                    for i in range(m):
                        w = words_list[i] or {}
                        c = chords_list[i] or {}
                        lyric = str(w.get("text", ""))
                        w_start = float(w.get("start_sec", 0.0)) + start_s
                        w_end = float(w.get("end_sec", 0.0)) + start_s
                        sym = c.get("symbol") or c.get("name") or ""
                        if not sym:
                            root = c.get("root") or ""
                            qual = c.get("quality") or ""
                            bass = c.get("bass") or ""
                            sym = root + (qual if qual else "") + ("/" + bass if bass else "")
                        rows.append((w_start, w_end, lyric, str(sym)))
                except Exception as e:
                    print(f"Note: parse error: {e}")
            if idx < len(parts):
                time.sleep(args.sleep_between)
        print(f"Total aligned rows: {len(rows)}")
        print("start\tend\tlyric\tchord")
        for s, e, lyr, ch in rows:
            print(f"{s:.3f}\t{e:.3f}\t{lyr}\t{ch}")
        return 0
    else:
        prompt = (
            "Rewrite this transcript as improved lyrics, keep word count the same where possible. "
            "Return STRICT JSON array of objects {text}. No prose, no code fences.\n\n" + args.text
        )
        res = call_gemini_text(api_key, args.model, prompt, timeout=args.timeout)
        print(f"HTTP {res['status']}")
        head = (res["text"] or "")[:800]
        print("Response head:\n" + head)
        if res["json"] is not None:
            try:
                cand = res["json"]["candidates"][0]["content"]["parts"][0]["text"]
                print("Candidate text head:\n" + cand[:800])
            except Exception as e:
                print(f"Note: could not parse candidate text: {e}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())


