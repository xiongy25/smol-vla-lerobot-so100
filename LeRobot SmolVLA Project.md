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

### 5. Eval smolvla policy with language command
```bash
python -m lerobot.record   --robot.type=so100_follower   --robot.port=/dev/tty_left_follower   --robot.id=blue   --robot.cameras='{
    "top": {"type": "opencv", "index_or_path": 0, "fps": 30, "width": 640, "height": 360},
    "gripper": {"type": "opencv", "index_or_path": 2, "fps": 30, "width": 640, "height": 360}
  }'   --policy.path=/home/ajinkya/Desktop/Robot/smolvla/lerobot/outputs/train/2025-06-09/13-58-02_smolvla/checkpoints/last/pretrained_model/   --dataset.repo_id=ajinkya/eval_smolvla-local-test   --dataset.num_episodes=3   --dataset.single_task="Grab the green wire and put in yellow basket"   --dataset.video=true   --display_data=true

```


## Notes
- The main data collection and policy execution commands (`python -m lerobot.record ...`) require correct CUDA/GPU setup and may fail if the environment is not properly configured.
- For calibration, ensure you provide either `--robot.*` or `--teleop.*` arguments, but not both.
- If you encounter errors, check the troubleshooting section or reach out for help. 



# 🤖 LeRobot SmolVLA Pipeline: LEGO Pick & Place with SO100 Robot

This repository documents a complete workflow using the `lerobot` library to train and evaluate robot policies using imitation learning. The task involves **picking a yellow LEGO cube** and **placing it inside a white LEGO frame** using the **SO100 follower robot**.

---

## 📌 Task

**Action**: `Pick the yellow LEGO cube and place it inside the white LEGO frame`  
**Robot**: `SO100`  
**Camera Views**: `top`, `gripper`  
**Control**: Human via SO100 teleoperation

---

## 🧭 Naming Convention

| Element        | Format                                    | Example                                      |
|----------------|-------------------------------------------|----------------------------------------------|
| Task Name      | `verb_object_target`                      | `lego_pick_place`                            |
| Robot Type     | `so100`                                   | `so100`                                      |
| HF Username    | your HF handle                            | `triton7777`                                 |
| Data Purpose   | `teleop_train`, `policy_eval`             | `lego_pick_place_so100_teleop_train`         |
| Model Name     | `task_robot_smolvla`                      | `lego_pick_place_so100_smolvla`              |

---

## 🔧 Teleoperate Robot (Only Signals, No Save)

```bash
python -m lerobot.teleoperate \
  --robot.type=so100_follower \
  --robot.port=/dev/tty_left_follower \
  --robot.id=blue \
  --teleop.type=so100_leader \
  --teleop.port=/dev/tty_left_leader \
  --teleop.id=yellow \
  --robot.cameras='{
    "top": {"type": "opencv", "index_or_path": 0, "fps": 30, "width": 640, "height": 360},
    "gripper": {"type": "opencv", "index_or_path": 2, "fps": 30, "width": 640, "height": 360}
  }' \
  --display_data=true

