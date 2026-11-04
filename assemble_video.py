"""
assemble_video.py
-----------------
Assembles the 15 PNG slide frames into a single MP4 video using imageio.
Each slide is held for its specified duration at 24 fps with a 0.4s
crossfade transition between slides.

Requirements: imageio[ffmpeg]  (Python 3.13 compatible)
Run:  python assemble_video.py
"""

import sys
import os
import numpy as np
from pathlib import Path
from PIL import Image

# ── Config ─────────────────────────────────────────────────────────────────────
FPS        = 24
FRAMES_DIR = Path("results/frames")
OUTPUT     = Path("results/vivasayi_demo.mp4")
FADE_FRAMES= 10   # 10 frames = ~0.4s crossfade at 24fps

# Each slide and how many seconds to hold it
SLIDE_DURATIONS = {
    "slide_01_slide_title":           6,
    "slide_02_slide_problem":         8,
    "slide_03_slide_solution":        7,
    "slide_04_slide_app_ui":          9,
    "slide_05_slide_forecast_output": 10,
    "slide_06_slide_checklist":       9,
    "slide_07_slide_code_tool":       10,
    "slide_08_slide_code_agent":      9,
    "slide_09_slide_system_prompt":   9,
    "slide_10_slide_tests":           9,
    "slide_11_slide_architecture":    9,
    "slide_12_slide_demo_mode":       9,
    "slide_13_slide_verification":    8,
    "slide_14_slide_next_steps":      8,
    "slide_15_slide_closing":         7,
}

def get_ordered_slides():
    """Return slide paths in order, matching any file that starts with slide_NN_"""
    slides = []
    for i in range(1, 16):
        matches = sorted(FRAMES_DIR.glob(f"slide_{i:02d}_*.png"))
        if matches:
            slides.append(matches[0])
        else:
            print(f"  WARNING: slide {i:02d} not found in {FRAMES_DIR}")
    return slides

def crossfade(frame_a: np.ndarray, frame_b: np.ndarray, t: int, n: int) -> np.ndarray:
    """Blend frame_a → frame_b linearly. t=0 → pure A, t=n → pure B."""
    alpha = t / n
    return (frame_a * (1 - alpha) + frame_b * alpha).astype(np.uint8)

def img_to_array(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)

def main():
    try:
        import imageio
    except ImportError:
        print("imageio not installed. Run: pip install imageio[ffmpeg] imageio-ffmpeg")
        sys.exit(1)

    OUTPUT.parent.mkdir(exist_ok=True)
    slides = get_ordered_slides()

    if not slides:
        print(f"No slides found in {FRAMES_DIR}. Run make_video.py first.")
        sys.exit(1)

    print(f"\nAssembling {len(slides)} slides → {OUTPUT}")
    print(f"FPS: {FPS}  |  Crossfade: {FADE_FRAMES} frames  |  Total: ~{sum(SLIDE_DURATIONS.values())}s\n")

    arrays = []
    print("Loading frames ...")
    for path in slides:
        arr = img_to_array(path)
        arrays.append(arr)
        print(f"  ✓  {path.name}  ({arr.shape[1]}×{arr.shape[0]})")

    # Get duration for each slide by matching slide number
    durations = []
    for path in slides:
        # Extract slide number from filename, e.g. slide_05_slide_forecast_output.png → 5
        try:
            num = int(path.stem.split("_")[1])
            dur = list(SLIDE_DURATIONS.values())[num - 1]
        except (IndexError, ValueError):
            dur = 8   # fallback 8s
        durations.append(dur)

    print(f"\nWriting {OUTPUT.resolve()} ...")

    writer = imageio.get_writer(
        str(OUTPUT),
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=None,
    )

    total_frames_written = 0

    for i, (arr, dur) in enumerate(zip(arrays, durations)):
        hold_frames = dur * FPS
        label = slides[i].stem
        print(f"  [{i+1:02d}/{len(slides)}]  {label:<45}  {dur}s  ({hold_frames} frames)", end="")

        # Hold this slide
        for _ in range(hold_frames):
            writer.append_data(arr)
            total_frames_written += 1

        # Crossfade to next slide
        if i < len(arrays) - 1:
            next_arr = arrays[i + 1]
            for t in range(1, FADE_FRAMES + 1):
                blended = crossfade(arr, next_arr, t, FADE_FRAMES)
                writer.append_data(blended)
                total_frames_written += 1

        print("  ✓")

    writer.close()

    # Stats
    total_seconds = total_frames_written / FPS
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)

    print(f"""
╔══════════════════════════════════════════════════════╗
║  ✅  VIDEO COMPLETE                                  ║
╠══════════════════════════════════════════════════════╣
║  File    :  results/vivasayi_demo.mp4                ║
║  Size    :  {size_mb:5.1f} MB                                  ║
║  Duration:  {total_seconds:5.0f}s  ({int(total_seconds)//60}m {int(total_seconds)%60}s)                      ║
║  Frames  :  {total_frames_written} @ {FPS}fps                      ║
║  Format  :  MP4 · H.264 · 1280×720 · no audio       ║
╚══════════════════════════════════════════════════════╝

To open the video:
  start results\\vivasayi_demo.mp4
""")

if __name__ == "__main__":
    main()
