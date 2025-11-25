import cv2
import numpy as np

# Detect available camera indices
max_tested = 10  # You can increase if you have more cameras
available_cams = []
for i in range(max_tested):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        available_cams.append(i)
        cap.release()

print(f"Available camera channels: {available_cams}")

if not available_cams:
    print("No cameras found.")
    exit(1)

# Open all cameras
caps = [cv2.VideoCapture(i) for i in available_cams]

# Set a target height for resizing
TARGET_HEIGHT = 240

while True:
    frames = []
    for cap in caps:
        ret, frame = cap.read()
        if not ret:
            frame = np.zeros((TARGET_HEIGHT, TARGET_HEIGHT, 3), dtype=np.uint8)
        else:
            h, w = frame.shape[:2]
            scale = TARGET_HEIGHT / h
            new_w = int(w * scale)
            frame = cv2.resize(frame, (new_w, TARGET_HEIGHT))
        frames.append(frame)
    # Pad frames to the same width
    max_width = max(f.shape[1] for f in frames)
    padded_frames = [cv2.copyMakeBorder(f, 0, 0, 0, max_width - f.shape[1], cv2.BORDER_CONSTANT, value=0) for f in frames]
    concat = np.hstack(padded_frames)
    cv2.imshow('All Cameras', concat)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

for cap in caps:
    cap.release()
cv2.destroyAllWindows() 