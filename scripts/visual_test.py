"""
TraceVision - Visual Match Verification Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Runs OSNet feature extraction on a reference query image,
searches against indexed tracks in Qdrant,
and draws bounding boxes and similarity scores on the video frame.
"""

import os
import sys
from pathlib import Path
import cv2

# Set up paths
ROOT_DIR = Path(__file__).resolve().parents[1]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine"
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from pipeline.query_processor import QueryProcessor


def run_visual_test():
    ref_image_path = ROOT_DIR / "person-detection" / "test_images" / "people.jpg"
    video_path = ROOT_DIR / "person-detection" / "test_videos" / "6387-191695740_medium.mp4"
    output_dir = ROOT_DIR / "outputs"
    output_dir.mkdir(exist_ok=True)
    output_image_path = output_dir / "test_match_visual.jpg"

    print("=" * 60)
    print("TraceVision: Visual Match Verification")
    print("=" * 60)
    print(f"Target Reference: {ref_image_path}")
    print(f"Target Video:     {video_path}")
    print("Executing similarity search in Qdrant...")

    qp = QueryProcessor()
    matches = qp.search_person(str(ref_image_path), limit=5, threshold=0.30)

    if not matches:
        print("No matches found above threshold!")
        return

    print(f"\nTop {len(matches)} Matches Retrieved:")
    for m in matches:
        score_pct = round(m["similarity_score"] * 100, 1)
        print(f"  • Rank {m['rank']}: Similarity = {score_pct}%, Track ID = {m['track_id']}, Timestamp = {m['timestamp']}s, BBox = {m['bbox']}")

    top_match = matches[0]
    matched_timestamp = top_match["timestamp"]
    bbox = top_match["bbox"]
    score_pct = round(top_match["similarity_score"] * 100, 1)
    track_id = top_match["track_id"]

    # Open video and jump to matched timestamp
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return

    cap.set(cv2.CAP_PROP_POS_MSEC, matched_timestamp * 1000)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print(f"Could not extract frame at timestamp {matched_timestamp}s")
        return

    # Draw bounding box (green)
    x1, y1, x2, y2 = bbox
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # Draw label badge with dark background
    label = f"Match: Track {track_id} ({score_pct}%) @ {matched_timestamp}s"
    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.rectangle(frame, (x1, max(0, y1 - 30)), (x1 + w + 10, y1), (0, 0, 0), -1)
    cv2.putText(
        frame,
        label,
        (x1 + 5, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

    cv2.imwrite(str(output_image_path), frame)
    print("\n" + "=" * 60)
    print(f"SUCCESS: Visual match saved to:")
    print(f"  {output_image_path}")
    print("=" * 60)


if __name__ == "__main__":
    run_visual_test()
