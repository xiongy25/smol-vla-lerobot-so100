import time
from pathlib import Path
from pprint import pformat

from lerobot.common.policies.factory import make_policy
from lerobot.common.robots import make_robot_from_config
from lerobot.common.datasets.utils import build_dataset_frame
from lerobot.common.utils.control_utils import predict_action
from lerobot.common.utils.utils import get_safe_torch_device, init_logging, log_say
from lerobot.configs.policies import PreTrainedConfig

# --- USER CONFIGURABLE ---
ROBOT_CONFIG = {
    'type': 'so100_follower',
    'port': '/dev/tty_left_follower',
    'id': 'blue',
    'cameras': {
        'top': {'type': 'opencv', 'index_or_path': 0, 'fps': 30, 'width': 640, 'height': 480},
        'gripper': {'type': 'opencv', 'index_or_path': 2, 'fps': 30, 'width': 640, 'height': 480},
    },
}
POLICY_PATH = "/home/ajinkya/Desktop/Robot/smolvla/outputs/train/2025-06-09/13-58-02_smolvla/checkpoints/last/pretrained_model/"
FPS = 10
EPISODE_TIME_S = 60  # Default max time per task
# ------------------------

def main():
    init_logging()
    print("Initializing robot...")
    robot = make_robot_from_config(ROBOT_CONFIG)
    print("Loading SmolVLA policy from", POLICY_PATH)
    policy_cfg = PreTrainedConfig.from_pretrained(POLICY_PATH)
    policy = make_policy(policy_cfg)
    robot.connect()
    print("Robot and policy ready.")

    try:
        while True:
            task_text = input("Enter task text (or 'q' to quit): ").strip()
            if task_text.lower() == 'q':
                break
            print(f"Running task: {task_text}")
            policy.reset()
            start_t = time.perf_counter()
            timestamp = 0
            while timestamp < EPISODE_TIME_S:
                loop_start = time.perf_counter()
                observation = robot.get_observation()
                # Build observation frame as in record.py
                observation_frame = build_dataset_frame(robot.observation_features, observation, prefix="observation")
                # Predict action
                action_values = predict_action(
                    observation_frame,
                    policy,
                    get_safe_torch_device(policy.config.device),
                    policy.config.use_amp,
                    task=task_text,
                    robot_type=robot.robot_type,
                )
                action = {key: action_values[i].item() for i, key in enumerate(robot.action_features)}
                sent_action = robot.send_action(action)
                print(f"Action: {sent_action}")
                dt = time.perf_counter() - loop_start
                time.sleep(max(0, 1/FPS - dt))
                timestamp = time.perf_counter() - start_t
            print(f"Task '{task_text}' completed.\n")
    finally:
        robot.disconnect()
        print("Robot disconnected. Exiting.")

if __name__ == "__main__":
    main() 