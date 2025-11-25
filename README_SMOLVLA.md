# LeRobot SmolVLA Project

This project contains code and utilities for controlling and calibrating the SO100Follower robot, managing datasets, and running vision-language models for robotic tasks.

---

## Successfully Tested Commands

### 1. Calibrate the Robot
```bash
python -m lerobot.calibrate \
  --robot.type=so100_follower \
  --robot.port=/dev/tty_left_follower \
  --robot.id=blue
```
**Result:**
- Runs the calibration procedure for the SO100Follower robot.
- Prompts for manual movement and saves calibration to `~/.cache/huggingface/lerobot/calibration/robots/so100_follower/blue.json`.

---

### 2. List Available Cameras
```bash
python utilities/show_all_cameras.py
```
**Result:**
- Lists available camera channels (e.g., `[0, 2]`).
- Useful for verifying which camera indices are available for use.

---

### 3. Remove Dataset Directory
```bash
rm -r /home/ajinkya/.cache/huggingface/lerobot/ajinkya/eval_smolvla-local-test
```
**Result:**
- Deletes the specified dataset directory to allow for fresh dataset creation.

---

### 4. List Directory Contents
```bash
ls
ls lerobot/
```
**Result:**
- Lists files and directories in the current and `lerobot/` directories.

---

## Notes
- The main data collection and policy execution commands (`python -m lerobot.record ...`) require correct CUDA/GPU setup and may fail if the environment is not properly configured.
- For calibration, ensure you provide either `--robot.*` or `--teleop.*` arguments, but not both.
- If you encounter errors, check the troubleshooting section or reach out for help. 