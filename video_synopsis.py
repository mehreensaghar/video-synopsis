"""
Video Synopsis with YOLOv8
Condenses long surveillance footage into a short video that keeps only
the moments where people appear.

Usage:
    python video_synopsis.py --input waiting_area.mp4 --output synopsis.mp4
"""
import argparse

import cv2
from ultralytics import YOLO

PERSON_CLASS = 0  # COCO class id for "person"


def build_synopsis(input_path, output_path, conf=0.4, skip=3, output_fps=60,
                   model_name="yolov8n.pt"):
    model = YOLO(model_name)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    input_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"),
                          output_fps, (width, height))

    frame_count = kept_frames = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count % skip != 0:          # sample every Nth frame
            continue

        results = model.track(frame, persist=True, conf=conf, verbose=False)
        boxes = results[0].boxes
        if len(boxes) > 0 and PERSON_CLASS in boxes.cls:   # keep frames with people
            out.write(results[0].plot())     # draw boxes + tracking IDs
            kept_frames += 1

        if frame_count % 200 == 0:
            print(f"Processed {frame_count}/{total_frames} frames...")

    cap.release()
    out.release()

    original_min = total_frames / input_fps / 60
    synopsis_min = kept_frames / output_fps / 60
    print(f"Original duration : {original_min:.2f} min")
    print(f"Synopsis duration : {synopsis_min:.2f} min")
    if synopsis_min:
        print(f"Compression ratio : {original_min / synopsis_min:.2f}x")
    print(f"Idle frames removed: {100 * (1 - kept_frames / total_frames):.2f}%")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Create a person-only video synopsis")
    p.add_argument("--input", required=True, help="path to the input video")
    p.add_argument("--output", default="synopsis.mp4")
    p.add_argument("--conf", type=float, default=0.4, help="detection confidence")
    p.add_argument("--skip", type=int, default=3, help="process every Nth frame")
    p.add_argument("--fps", type=int, default=60, help="output playback FPS")
    a = p.parse_args()
    build_synopsis(a.input, a.output, a.conf, a.skip, a.fps)
