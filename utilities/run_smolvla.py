import os
import sys
import time
import cv2
import torch
import numpy as np
from pathlib import Path

# Import SmolVLA policy and config
from lerobot.common.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.common.policies.smolvla.configuration_smolvla import SmolVLAConfig

# Set your checkpoint path here
CHECKPOINT_PATH = "/home/ajinkya/Desktop/Robot/smolvla/outputs/train/2025-06-09/13-58-02_smolvla/checkpoints/last/pretrained_model/"

# Camera indices (adjust as needed)
CAMERA_CONFIG = {
    "top": 0,
    "gripper": 2
}

# Camera resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Load the SmolVLA policy
print(f"Loading SmolVLA model from {CHECKPOINT_PATH}")
policy = SmolVLAPolicy.from_pretrained(CHECKPOINT_PATH)

# Open cameras
caps = {name: cv2.VideoCapture(idx) for name, idx in CAMERA_CONFIG.items()}
for cap in caps.values():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

print("Cameras opened:", CAMERA_CONFIG)

# Main loop for task execution
while True:
    task_text = input("Enter task text (or 'q' to quit): ").strip()
    if task_text.lower() == 'q':
        break
    print(f"Running task: {task_text}")

    # Example: Run for a fixed number of steps (replace with your robot control loop)
    for step in range(50):
        # Read images from all cameras
        images = {}
        for name, cap in caps.items():
            ret, frame = cap.read()
            if not ret:
                frame = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
            images[name] = frame

        # Preprocess images as expected by SmolVLA (resize, normalize, etc.)
        # Here, just stack as batch of images for demonstration
        # You may need to adapt this to match your model's expected input
        batch = {
            f"observation.images.{name}": torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).permute(2,0,1).unsqueeze(0).float() / 255.0
            for name, img in images.items()
        }
        # Add task text as language input
        batch["observation.language"] = [task_text]

        # Run the policy (forward pass)
        with torch.no_grad():
            try:
                action = policy(batch)
            except Exception as e:
                print(f"Model error: {e}")
                break
        # Here you would send 'action' to your robot
        print(f"Step {step+1}: Action output: {action}")
        time.sleep(0.1)  # Simulate control loop delay

    print(f"Task '{task_text}' completed.\n")

# Release cameras
for cap in caps.values():
    cap.release()
cv2.destroyAllWindows()
print("Exited.") 