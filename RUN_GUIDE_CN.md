<!-- cSpell:ignoreFile -->
<!-- markdownlint-disable MD031 MD012 -->

# SmolVLA / SO100 项目运行指南

本文总结了在本地环境中跑通 `smolvla-lerobot` 项目的关键步骤，包括环境准备、硬件接线、数据采集、策略训练与评估等。文中的命令均可在项目根目录下执行，可按需替换端口与路径。

## 1. 环境准备

1. 创建 Python 3.10 虚拟环境并安装依赖（本项目已包含完整的 lerobot 代码，无需克隆仓库。如需离线部署，提前把依赖包下载到本地镜像或 `pip download` 成 wheels 后在此目录安装）：

   ```bash
   # 在项目根目录下执行（无需克隆仓库，项目已包含 lerobot）
   conda create -y -n lerobot python=3.10
   conda activate lerobot
   conda install ffmpeg -c conda-forge
   pip install -e .
   ```

2. 根据硬件选择可选依赖，例如 SO100/101 机器人需要 Feetech SDK：

   ```bash
   pip install -e ".[feetech]"
   ```

3. 若需仿真环境、实验追踪等，可在 `pip install -e ".[aloha,xarm,pusht]"` 与 `wandb login` 之间按需选择；完全离线时将后者改为 `export WANDB_MODE=offline`（Windows 为 `set WANDB_MODE=offline`）。
4. 如果需要访问 Hugging Face Hub，再执行登录；若只在本地使用，可跳过此步骤并在运行脚本前设置 HF 离线变量（见下方提示）：

   ```bash
   huggingface-cli login --token <WRITE_TOKEN> --add-to-git-credential
   HF_USER=$(huggingface-cli whoami | head -n 1)
   ```

> 提示：完全离线时，可提前下载好权重/数据并设置  
> `export HF_HOME=/path/to/cache && export HF_DATASETS_OFFLINE=1 && export HF_HUB_OFFLINE=1 && export TRANSFORMERS_OFFLINE=1`  
> 这样脚本会优先读取本地缓存而不会尝试联网。（PowerShell 对应 `setx HF_DATASETS_OFFLINE 1` 等命令。）  
> 若编译依赖缺失，可参考 `docs/source/installation.mdx` 中的故障排除部分安装 `cmake`、`build-essential` 等。

## 2. 硬件连接与校准

1. **识别串口**：连接电源与 USB，运行

   ```bash
   python lerobot/find_port.py
   ```

   根据提示拔插设备即可得到 follower 与 leader 各自的串口。
2. **写入电机 ID / 波特率**：依次独立连接各关节电机，执行

   ```bash
   python -m lerobot.setup_motors \
     --robot.type=so100_follower \
     --robot.port=/dev/ttyACM1 \
     --robot.id=blue
   python -m lerobot.setup_motors \
     --teleop.type=so100_leader \
     --teleop.port=/dev/ttyACM0 \
     --teleop.id=yellow
   ```

3. **校准**：将各关节置于中位并按提示操作

   ```bash
   python -m lerobot.calibrate \
     --robot.type=so100_follower \
     --robot.port=/dev/ttyACM1 \
     --robot.id=blue
   python -m lerobot.calibrate \
     --teleop.type=so100_leader \
     --teleop.port=/dev/ttyACM0 \
     --teleop.id=yellow
   ```

   校准文件会保存到 `~/.cache/huggingface/lerobot/calibration/...`，后续 teleoperate / record / replay 均需复用相同 `id`。
4. **摄像头排查**：通过

   ```bash
   python utilities/show_all_cameras.py
   ```

   确认可用的 `index_or_path`，记录 `width/height/fps` 等配置。

## 3. 快速自检命令

- 仅驱动机器人执行校准或动作：

  ```bash
  python -m lerobot.teleoperate \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM1 \
    --robot.id=blue \
    --teleop.type=so100_leader \
    --teleop.port=/dev/ttyACM0 \
    --teleop.id=yellow \
    --robot.cameras='{
      "top": {"type": "opencv", "index_or_path": 0, "fps": 30, "width": 640, "height": 360},
      "gripper": {"type": "opencv", "index_or_path": 2, "fps": 30, "width": 640, "height": 360}
    }' \
    --display_data=true
  ```

- 删除受损数据集重新录制：

  ```bash
  rm -r ~/.cache/huggingface/lerobot/<repo_id>
  ```

- 如果命令没有硬件输入（如 `--teleop.*`），请确保只提供 `--robot.*` 参数，反之亦然。

## 4. 数据录制流程

1. 配置摄像头 JSON（可直接在命令行字符串中书写或保存成文件后通过 `@file.json` 传入）。
2. 运行录制脚本（以下示例采集 2 个 episode 并推送到 Hugging Face）：

   ```bash
   python -m lerobot.record \
     --robot.type=so100_follower \
     --robot.port=/dev/ttyACM1 \
     --robot.id=blue \
     --robot.cameras='{
       "top": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 360, "fps": 30},
       "gripper": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 360, "fps": 30}
     }' \
     --teleop.type=so100_leader \
     --teleop.port=/dev/ttyACM0 \
     --teleop.id=yellow \
     --display_data=true \
     --dataset.repo_id=${HF_USER}/lego_pick_place_so100_teleop_train \
     --dataset.num_episodes=2 \
     --dataset.single_task="Pick the yellow LEGO cube and drop into white frame" \
     --dataset.video=true
   ```
3. 录制过程中可使用快捷键：右箭头提前结束当前 episode，左箭头重录，`Esc` 立即停止并上传。
4. 数据默认落在 `~/.cache/huggingface/lerobot/<repo-id>`；本仓库已预置 `data/lerobot_cache` 目录，可直接作为本地缓存根。推荐在启动终端后执行 `export HF_HOME=$PWD/data/lerobot_cache`（PowerShell: `set HF_HOME=%CD%\\data\\lerobot_cache%`），或在命令中追加 `--dataset.root=$PWD/data/lerobot_cache`。同时设置 `--dataset.push_to_hub=false` 可只保存在本地；训练或回放时传入相同的 `--dataset.repo_id`（即使未登录 HF）即可自动读取该目录。

## 5. 训练 SmolVLA 策略

1. 使用 `lerobot/scripts/train.py`，指定数据集与策略类型：

   ```bash
   python lerobot/scripts/train.py \
     --dataset.repo_id=${HF_USER:-local_user}/lego_pick_place_so100_teleop_train \
     --dataset.root=$PWD/data/lerobot_cache \
     --dataset.push_to_hub=false \
     --policy.type=act \
     --output_dir=outputs/train/lego_pick_place_so100_smolvla \
     --job_name=lego_pick_place_so100_smolvla \
     --policy.device=cuda \
     --wandb.enable=false
   ```
2. 关键参数说明：
   - `--dataset.repo_id`：可为本地缓存或 Hugging Face dataset repo。
   - `--policy.type`：ACT、Diffusion 等，具体配置见 `lerobot/common/policies/*`.
   - `--output_dir` / `--job_name`：决定日志与 checkpoint 目录。
- `--policy.device`：`cuda`、`cpu`、`mps`，需和硬件匹配。
- `--wandb.enable`：本地训练建议设为 `false`，或使用 `WANDB_MODE=offline`。
3. 训练中会在 `outputs/train/.../checkpoints/{step}/pretrained_model` 下生成模型；可通过

   ```bash
   python lerobot/scripts/train.py \
     --config_path=outputs/train/.../checkpoints/last/pretrained_model/train_config.json \
     --resume=true
   ```

   继续训练。
4. 训练完成后，如需联网可再执行：

   ```bash
   huggingface-cli upload ${HF_USER}/lego_pick_place_so100_smolvla \
     outputs/train/lego_pick_place_so100_smolvla/checkpoints/last/pretrained_model
   ```

## 6. 评估与回放

1. **策略评估（录制评估集并自动推送）**：

   ```bash
   python -m lerobot.record \
     --robot.type=so100_follower \
     --robot.port=/dev/ttyACM1 \
     --robot.id=blue \
     --robot.cameras='{
       "top": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 360, "fps": 30},
       "gripper": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 360, "fps": 30}
     }' \
     --teleop.type=so100_leader \
     --teleop.port=/dev/ttyACM0 \
     --teleop.id=yellow \
     --display_data=false \
     --dataset.repo_id=${HF_USER}/eval_smolvla_local \
     --dataset.num_episodes=10 \
     --dataset.single_task="Evaluation: pick and place" \
     --policy.path=outputs/train/lego_pick_place_so100_smolvla/checkpoints/last/pretrained_model
   ```

   与录制阶段相比仅增加了 `--policy.path`（或直接指向 HF 模型仓库），并建议将 `repo_id` 命名为 `eval_*`。
2. **回放指定 episode**：

   ```bash
   python -m lerobot.replay \
     --robot.type=so100_follower \
     --robot.port=/dev/ttyACM1 \
     --robot.id=blue \
     --dataset.repo_id=${HF_USER}/lego_pick_place_so100_teleop_train \
     --dataset.episode=0
   ```
3. 若需要仅运行策略进行在线演示，可将 `--dataset.*` 参数替换为 `--control.*` 相关设置，或改用 `lerobot/run_smolvla_robot.py` 自行编写脚本。

## 7. 完全离线运行清单

1. **依赖准备**：提前下载 pip/conda 包或放置在本地镜像；安装后不再访问外网。
2. **HF 缓存**：使用 `data/lerobot_cache` 作为统一缓存根；联网机器将所需数据/模型放入该目录后复制到离线环境，运行前 `export HF_HOME=$PWD/data/lerobot_cache` 并导出 `HF_*_OFFLINE=1`。
3. **数据录制**：所有 `lerobot.record` 命令添加 `--dataset.root=$PWD/data/lerobot_cache --dataset.push_to_hub=false`，方便在项目内直接共享。
4. **训练配置**：`--wandb.enable=false`、`WANDB_MODE=offline`，并优先使用本地 `--config_path` 或 `outputs/train/.../train_config.json`。如需要多机复现，可把配置与 checkpoint 打包。
5. **评估/回放**：与训练相同，引用本地缓存或 `--policy.path=/path/to/checkpoint`，确保不包含远程 repo 地址。
6. **可选联网步骤**：上传模型、登录 HF、`wandb login` 等都可延后到有网络的环境执行。

## 8. 故障排查与建议

- **GPU / CUDA 相关报错**：`python -m lerobot.record ...` 需要可用的 CUDA 驱动与显卡，若在 CPU 环境可尝试降低摄像头数量或分辨率。
- **数据损坏**：删除 `~/.cache/huggingface/lerobot/<repo-id>` 后重新录制即可。
- **键盘控制无效**：Linux 下需设置 `$DISPLAY`，参考 `pynput` 依赖限制。
- **摄像头帧率异常**：先使用 `utilities/show_all_cameras.py` 确认索引，再在命令中传入匹配的 `fps/width/height`。
- **需要更多样例**：可参考 `examples/` 目录中的脚本（如 `2_evaluate_pretrained_policy.py`）快速了解 API 用法。

按照以上步骤即可完成 SO100 SmolVLA 任务的完整闭环：硬件连接 → 数据录制 → 策略训练 → 评估与回放。如需更多细节，可查阅 `docs/source` 中的安装、相机、机器人说明文档或加入官方 Discord 获取支持。

