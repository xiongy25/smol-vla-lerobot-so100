#!/usr/bin/env python3
"""
LeRobot SO100 GUI - 图形化界面工具
用于简化 RUN_GUIDE_CN.md 中各种命令的执行
"""

import json
import os
import platform
import subprocess
import sys
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QPushButton, QLineEdit, QLabel, QTextEdit, QGroupBox,
        QSpinBox, QCheckBox, QFileDialog, QMessageBox, QComboBox
    )
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtGui import QFont, QTextCursor
except ImportError:
    print("PySide6 未安装。请运行: pip install PySide6")
    sys.exit(1)


class CommandRunner(QThread):
    """在后台线程中运行命令，避免阻塞 GUI"""
    output = Signal(str)
    finished = Signal(int)  # 返回退出码

    def __init__(
        self, command: list, cwd: Optional[str] = None,
        env: Optional[dict] = None
    ):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.env = env or os.environ.copy()

    def run(self):
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.cwd,
                env=self.env,
                shell=platform.system() == "Windows"
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.output.emit(line.rstrip())
            
            process.wait()
            self.finished.emit(process.returncode)
        except Exception as e:
            self.output.emit(f"错误: {str(e)}")
            self.finished.emit(1)


class BaseCommandWidget(QWidget):
    """基础命令执行组件，包含输出显示区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.runner: Optional[CommandRunner] = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 输出显示区域
        output_group = QGroupBox("📋 命令输出")
        output_group.setObjectName("outputGroup")
        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(10, 15, 10, 10)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setObjectName("outputText")
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        # 设置输出区域的最大高度，避免占据所有空间
        self.output_text.setMaximumHeight(400)
        layout.addWidget(output_group, 1)  # 拉伸因子为1，占据剩余空间
        
        # 清空输出按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        clear_btn = QPushButton("🗑️ 清空输出")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self.output_text.clear)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
    
    def append_output(self, text: str):
        """追加输出文本"""
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
        self.output_text.insertPlainText(text + "\n")
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def run_command(
        self, command: list, cwd: Optional[str] = None,
        env: Optional[dict] = None
    ):
        """运行命令"""
        if self.runner and self.runner.isRunning():
            QMessageBox.warning(
                self, "警告", "命令正在运行中，请等待完成。"
            )
            return

        # 显示命令
        cmd_str = " ".join(command) if isinstance(command, list) else command
        self.append_output(f">>> {cmd_str}\n")

        self.runner = CommandRunner(command, cwd, env)
        self.runner.output.connect(self.append_output)
        self.runner.finished.connect(
            lambda code: self.append_output(
                f"\n[命令完成，退出码: {code}]\n"
            )
        )
        self.runner.start()


class EnvironmentSetupWidget(BaseCommandWidget):
    """环境准备模块"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_environment_ui()
    
    def setup_environment_ui(self):
        # 在输出区域之前插入配置区域
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        main_layout = self.layout()
        
        # 提示信息：项目已包含 lerobot
        info_label = QLabel("ℹ️ 提示：本项目已包含完整的 lerobot 代码，无需克隆仓库。")
        info_label.setObjectName("infoLabel")
        info_label.setWordWrap(True)
        config_layout.addWidget(info_label)
        
        # 创建虚拟环境
        env_group = QGroupBox("🐍 1. 创建 Conda 虚拟环境")
        env_group.setObjectName("configGroup")
        env_layout = QVBoxLayout()
        env_layout.setSpacing(10)
        env_layout.setContentsMargins(15, 20, 15, 15)
        env_layout.addWidget(QLabel("环境名称:"))
        self.env_name = QLineEdit("lerobot")
        self.env_name.setObjectName("inputField")
        env_layout.addWidget(self.env_name)
        env_layout.addWidget(QLabel("Python 版本:"))
        self.python_version = QLineEdit("3.10")
        self.python_version.setObjectName("inputField")
        env_layout.addWidget(self.python_version)
        create_env_btn = QPushButton("✨ 创建环境")
        create_env_btn.setObjectName("primaryButton")
        create_env_btn.clicked.connect(self.create_env)
        env_layout.addWidget(create_env_btn)
        env_group.setLayout(env_layout)
        config_layout.addWidget(env_group)
        
        # 安装依赖
        install_group = QGroupBox("📚 2. 安装依赖")
        install_group.setObjectName("configGroup")
        install_layout = QVBoxLayout()
        install_layout.setSpacing(10)
        install_layout.setContentsMargins(15, 20, 15, 15)
        self.extra_deps = QLineEdit("feetech")
        self.extra_deps.setObjectName("inputField")
        install_layout.addWidget(
            QLabel("额外依赖 (逗号分隔，如: feetech,aloha):")
        )
        install_layout.addWidget(self.extra_deps)
        install_btn = QPushButton("📥 安装依赖")
        install_btn.setObjectName("primaryButton")
        install_btn.clicked.connect(self.install_deps)
        install_layout.addWidget(install_btn)
        install_group.setLayout(install_layout)
        config_layout.addWidget(install_group)

        # 将配置布局插入到输出区域之前（索引0）
        main_layout.insertLayout(0, config_layout)
    
    def create_env(self):
        env_name = self.env_name.text() or "lerobot"
        python_ver = self.python_version.text() or "3.10"
        cmd = [
            "conda", "create", "-y", "-n", env_name, f"python={python_ver}"
        ]
        # 注意：实际使用时需要激活环境，这里简化处理
        self.append_output("注意: 请手动激活环境后再安装依赖")
        self.run_command(cmd)
    
    def install_deps(self):
        extra = self.extra_deps.text().strip()
        # 获取项目根目录（GUI 脚本所在目录）
        project_root = os.path.dirname(os.path.abspath(__file__))
        if extra:
            deps = ",".join([d.strip() for d in extra.split(",")])
            cmd = ["pip", "install", "-e", f".[{deps}]"]
        else:
            cmd = ["pip", "install", "-e", "."]
        # 确保在项目根目录下执行安装命令
        self.run_command(cmd, cwd=project_root)


class HardwareSetupWidget(BaseCommandWidget):
    """硬件连接与校准模块"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_hardware_ui()
    
    def setup_hardware_ui(self):
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        main_layout = self.layout()
        
        # 查找端口
        port_group = QGroupBox("🔍 1. 查找串口")
        port_group.setObjectName("configGroup")
        port_layout = QVBoxLayout()
        port_layout.setSpacing(10)
        port_layout.setContentsMargins(15, 20, 15, 15)
        find_port_btn = QPushButton("🔎 查找端口")
        find_port_btn.setObjectName("primaryButton")
        find_port_btn.clicked.connect(
            lambda: self.run_command(["python", "lerobot/find_port.py"])
        )
        port_layout.addWidget(find_port_btn)
        port_group.setLayout(port_layout)
        config_layout.addWidget(port_group)
        
        # 设置电机
        motor_group = QGroupBox("⚙️ 2. 设置电机 ID")
        motor_group.setObjectName("configGroup")
        motor_layout = QVBoxLayout()
        motor_layout.setSpacing(10)
        motor_layout.setContentsMargins(15, 20, 15, 15)
        
        # Robot 设置
        robot_layout = QHBoxLayout()
        robot_layout.setSpacing(10)
        robot_layout.addWidget(QLabel("Robot 端口:"))
        self.robot_port = QLineEdit("/dev/ttyACM1")
        self.robot_port.setObjectName("inputField")
        robot_layout.addWidget(self.robot_port)
        robot_layout.addWidget(QLabel("ID:"))
        self.robot_id = QLineEdit("blue")
        self.robot_id.setObjectName("inputField")
        robot_layout.addWidget(self.robot_id)
        motor_layout.addLayout(robot_layout)
        setup_robot_btn = QPushButton("🤖 设置 Robot")
        setup_robot_btn.setObjectName("primaryButton")
        setup_robot_btn.clicked.connect(self.setup_robot)
        motor_layout.addWidget(setup_robot_btn)
        
        # Teleop 设置
        teleop_layout = QHBoxLayout()
        teleop_layout.setSpacing(10)
        teleop_layout.addWidget(QLabel("Teleop 端口:"))
        self.teleop_port = QLineEdit("/dev/ttyACM0")
        self.teleop_port.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_port)
        teleop_layout.addWidget(QLabel("ID:"))
        self.teleop_id = QLineEdit("yellow")
        self.teleop_id.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_id)
        motor_layout.addLayout(teleop_layout)
        setup_teleop_btn = QPushButton("🎮 设置 Teleop")
        setup_teleop_btn.setObjectName("primaryButton")
        setup_teleop_btn.clicked.connect(self.setup_teleop)
        motor_layout.addWidget(setup_teleop_btn)
        
        motor_group.setLayout(motor_layout)
        config_layout.addWidget(motor_group)
        
        # 校准
        calibrate_group = QGroupBox("🎯 3. 校准")
        calibrate_group.setObjectName("configGroup")
        calibrate_layout = QVBoxLayout()
        calibrate_layout.setSpacing(10)
        calibrate_layout.setContentsMargins(15, 20, 15, 15)
        calibrate_robot_btn = QPushButton("🔧 校准 Robot")
        calibrate_robot_btn.setObjectName("primaryButton")
        calibrate_robot_btn.clicked.connect(self.calibrate_robot)
        calibrate_layout.addWidget(calibrate_robot_btn)
        calibrate_teleop_btn = QPushButton("🔧 校准 Teleop")
        calibrate_teleop_btn.setObjectName("primaryButton")
        calibrate_teleop_btn.clicked.connect(self.calibrate_teleop)
        calibrate_layout.addWidget(calibrate_teleop_btn)
        calibrate_group.setLayout(calibrate_layout)
        config_layout.addWidget(calibrate_group)
        
        # 查看摄像头
        camera_group = QGroupBox("📷 4. 查看摄像头")
        camera_group.setObjectName("configGroup")
        camera_layout = QVBoxLayout()
        camera_layout.setSpacing(10)
        camera_layout.setContentsMargins(15, 20, 15, 15)
        show_cameras_btn = QPushButton("📹 显示所有摄像头")
        show_cameras_btn.setObjectName("primaryButton")
        show_cameras_btn.clicked.connect(
            lambda: self.run_command(
                ["python", "utilities/show_all_cameras.py"]
            )
        )
        camera_layout.addWidget(show_cameras_btn)
        camera_group.setLayout(camera_layout)
        config_layout.addWidget(camera_group)

        # 将配置布局插入到输出区域之前（索引0）
        main_layout.insertLayout(0, config_layout)
    
    def setup_robot(self):
        port = self.robot_port.text()
        robot_id = self.robot_id.text()
        cmd = [
            "python", "-m", "lerobot.setup_motors",
            "--robot.type=so100_follower",
            f"--robot.port={port}",
            f"--robot.id={robot_id}"
        ]
        self.run_command(cmd)

    def setup_teleop(self):
        port = self.teleop_port.text()
        teleop_id = self.teleop_id.text()
        cmd = [
            "python", "-m", "lerobot.setup_motors",
            "--teleop.type=so100_leader",
            f"--teleop.port={port}",
            f"--teleop.id={teleop_id}"
        ]
        self.run_command(cmd)
    
    def calibrate_robot(self):
        port = self.robot_port.text()
        robot_id = self.robot_id.text()
        cmd = [
            "python", "-m", "lerobot.calibrate",
            "--robot.type=so100_follower",
            f"--robot.port={port}",
            f"--robot.id={robot_id}"
        ]
        self.run_command(cmd)
    
    def calibrate_teleop(self):
        port = self.teleop_port.text()
        teleop_id = self.teleop_id.text()
        cmd = [
            "python", "-m", "lerobot.calibrate",
            "--teleop.type=so100_leader",
            f"--teleop.port={port}",
            f"--teleop.id={teleop_id}"
        ]
        self.run_command(cmd)


class TeleoperateWidget(BaseCommandWidget):
    """遥操作模块"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_teleoperate_ui()
    
    def setup_teleoperate_ui(self):
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        main_layout = self.layout()
        
        # 机器人配置
        robot_group = QGroupBox("🤖 机器人配置")
        robot_group.setObjectName("configGroup")
        robot_layout = QVBoxLayout()
        robot_layout.setSpacing(10)
        robot_layout.setContentsMargins(15, 20, 15, 15)
        robot_layout.addWidget(QLabel("端口:"))
        self.robot_port = QLineEdit("/dev/ttyACM1")
        self.robot_port.setObjectName("inputField")
        robot_layout.addWidget(self.robot_port)
        robot_layout.addWidget(QLabel("ID:"))
        self.robot_id = QLineEdit("blue")
        self.robot_id.setObjectName("inputField")
        robot_layout.addWidget(self.robot_id)
        robot_group.setLayout(robot_layout)
        config_layout.addWidget(robot_group)
        
        # Teleop 配置
        teleop_group = QGroupBox("🎮 Teleop 配置")
        teleop_group.setObjectName("configGroup")
        teleop_layout = QVBoxLayout()
        teleop_layout.setSpacing(10)
        teleop_layout.setContentsMargins(15, 20, 15, 15)
        teleop_layout.addWidget(QLabel("端口:"))
        self.teleop_port = QLineEdit("/dev/ttyACM0")
        self.teleop_port.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_port)
        teleop_layout.addWidget(QLabel("ID:"))
        self.teleop_id = QLineEdit("yellow")
        self.teleop_id.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_id)
        teleop_group.setLayout(teleop_layout)
        config_layout.addWidget(teleop_group)
        
        # 摄像头配置
        camera_group = QGroupBox("📷 摄像头配置")
        camera_group.setObjectName("configGroup")
        camera_layout = QVBoxLayout()
        camera_layout.setSpacing(10)
        camera_layout.setContentsMargins(15, 20, 15, 15)
        camera_layout.addWidget(QLabel("Top 摄像头索引:"))
        self.top_cam_idx = QLineEdit("0")
        self.top_cam_idx.setObjectName("inputField")
        camera_layout.addWidget(self.top_cam_idx)
        camera_layout.addWidget(QLabel("Gripper 摄像头索引:"))
        self.gripper_cam_idx = QLineEdit("2")
        self.gripper_cam_idx.setObjectName("inputField")
        camera_layout.addWidget(self.gripper_cam_idx)
        self.display_data = QCheckBox("显示数据")
        self.display_data.setChecked(True)
        camera_layout.addWidget(self.display_data)
        camera_group.setLayout(camera_layout)
        config_layout.addWidget(camera_group)

        # 运行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        run_btn = QPushButton("▶️ 开始遥操作")
        run_btn.setObjectName("actionButton")
        run_btn.clicked.connect(self.run_teleoperate)
        btn_layout.addWidget(run_btn)
        config_layout.addLayout(btn_layout)

        # 将配置布局插入到输出区域之前（索引0）
        main_layout.insertLayout(0, config_layout)
    
    def run_teleoperate(self):
        cameras_json = {
            "top": {
                "type": "opencv",
                "index_or_path": int(self.top_cam_idx.text()),
                "fps": 30,
                "width": 640,
                "height": 360
            },
            "gripper": {
                "type": "opencv",
                "index_or_path": int(self.gripper_cam_idx.text()),
                "fps": 30,
                "width": 640,
                "height": 360
            }
        }

        cmd = [
            "python", "-m", "lerobot.teleoperate",
            "--robot.type=so100_follower",
            f"--robot.port={self.robot_port.text()}",
            f"--robot.id={self.robot_id.text()}",
            "--teleop.type=so100_leader",
            f"--teleop.port={self.teleop_port.text()}",
            f"--teleop.id={self.teleop_id.text()}",
            f"--robot.cameras={json.dumps(cameras_json)}",
            f"--display_data={str(self.display_data.isChecked()).lower()}"
        ]
        self.run_command(cmd)


class RecordWidget(BaseCommandWidget):
    """数据录制模块"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_record_ui()
    
    def setup_record_ui(self):
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        main_layout = self.layout()
        
        # 机器人配置
        robot_group = QGroupBox("🤖 机器人配置")
        robot_group.setObjectName("configGroup")
        robot_layout = QVBoxLayout()
        robot_layout.setSpacing(10)
        robot_layout.setContentsMargins(15, 20, 15, 15)
        robot_layout.addWidget(QLabel("端口:"))
        self.robot_port = QLineEdit("/dev/ttyACM1")
        self.robot_port.setObjectName("inputField")
        robot_layout.addWidget(self.robot_port)
        robot_layout.addWidget(QLabel("ID:"))
        self.robot_id = QLineEdit("blue")
        self.robot_id.setObjectName("inputField")
        robot_layout.addWidget(self.robot_id)
        robot_group.setLayout(robot_layout)
        config_layout.addWidget(robot_group)
        
        # Teleop 配置
        teleop_group = QGroupBox("🎮 Teleop 配置")
        teleop_group.setObjectName("configGroup")
        teleop_layout = QVBoxLayout()
        teleop_layout.setSpacing(10)
        teleop_layout.setContentsMargins(15, 20, 15, 15)
        teleop_layout.addWidget(QLabel("端口:"))
        self.teleop_port = QLineEdit("/dev/ttyACM0")
        self.teleop_port.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_port)
        teleop_layout.addWidget(QLabel("ID:"))
        self.teleop_id = QLineEdit("yellow")
        self.teleop_id.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_id)
        teleop_group.setLayout(teleop_layout)
        config_layout.addWidget(teleop_group)
        
        # 摄像头配置
        camera_group = QGroupBox("📷 摄像头配置")
        camera_group.setObjectName("configGroup")
        camera_layout = QVBoxLayout()
        camera_layout.setSpacing(10)
        camera_layout.setContentsMargins(15, 20, 15, 15)
        camera_layout.addWidget(QLabel("Top 摄像头索引:"))
        self.top_cam_idx = QLineEdit("0")
        self.top_cam_idx.setObjectName("inputField")
        camera_layout.addWidget(self.top_cam_idx)
        camera_layout.addWidget(QLabel("Gripper 摄像头索引:"))
        self.gripper_cam_idx = QLineEdit("2")
        self.gripper_cam_idx.setObjectName("inputField")
        camera_layout.addWidget(self.gripper_cam_idx)
        self.display_data = QCheckBox("显示数据")
        self.display_data.setChecked(True)
        camera_layout.addWidget(self.display_data)
        camera_group.setLayout(camera_layout)
        config_layout.addWidget(camera_group)
        
        # 数据集配置
        dataset_group = QGroupBox("💾 数据集配置")
        dataset_group.setObjectName("configGroup")
        dataset_layout = QVBoxLayout()
        dataset_layout.setSpacing(10)
        dataset_layout.setContentsMargins(15, 20, 15, 15)
        dataset_layout.addWidget(QLabel("Repo ID (用户名/数据集名):"))
        self.repo_id = QLineEdit(
            "local_user/lego_pick_place_so100_teleop_train"
        )
        self.repo_id.setObjectName("inputField")
        dataset_layout.addWidget(self.repo_id)
        dataset_layout.addWidget(QLabel("Episode 数量:"))
        self.num_episodes = QSpinBox()
        self.num_episodes.setMinimum(1)
        self.num_episodes.setValue(2)
        dataset_layout.addWidget(self.num_episodes)
        dataset_layout.addWidget(QLabel("任务描述:"))
        self.task_desc = QLineEdit(
            "Pick the yellow LEGO cube and drop into white frame"
        )
        self.task_desc.setObjectName("inputField")
        dataset_layout.addWidget(self.task_desc)
        self.video_enabled = QCheckBox("录制视频")
        self.video_enabled.setChecked(True)
        dataset_layout.addWidget(self.video_enabled)
        self.push_to_hub = QCheckBox("推送到 Hugging Face Hub")
        dataset_layout.addWidget(self.push_to_hub)
        dataset_group.setLayout(dataset_layout)
        config_layout.addWidget(dataset_group)

        # 运行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        run_btn = QPushButton("🎬 开始录制")
        run_btn.setObjectName("actionButton")
        run_btn.clicked.connect(self.run_record)
        btn_layout.addWidget(run_btn)
        config_layout.addLayout(btn_layout)

        # 将配置布局插入到输出区域之前（索引0）
        main_layout.insertLayout(0, config_layout)
    
    def run_record(self):
        cameras_json = {
            "top": {
                "type": "opencv",
                "index_or_path": int(self.top_cam_idx.text()),
                "fps": 30,
                "width": 640,
                "height": 360
            },
            "gripper": {
                "type": "opencv",
                "index_or_path": int(self.gripper_cam_idx.text()),
                "fps": 30,
                "width": 640,
                "height": 360
            }
        }

        cmd = [
            "python", "-m", "lerobot.record",
            "--robot.type=so100_follower",
            f"--robot.port={self.robot_port.text()}",
            f"--robot.id={self.robot_id.text()}",
            f"--robot.cameras={json.dumps(cameras_json)}",
            "--teleop.type=so100_leader",
            f"--teleop.port={self.teleop_port.text()}",
            f"--teleop.id={self.teleop_id.text()}",
            f"--display_data={str(self.display_data.isChecked()).lower()}",
            f"--dataset.repo_id={self.repo_id.text()}",
            f"--dataset.num_episodes={self.num_episodes.value()}",
            f"--dataset.single_task={self.task_desc.text()}",
            f"--dataset.video={str(self.video_enabled.isChecked()).lower()}"
        ]

        if not self.push_to_hub.isChecked():
            cmd.append("--dataset.push_to_hub=false")

        self.run_command(cmd)


class TrainWidget(BaseCommandWidget):
    """训练模块"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_train_ui()
    
    def setup_train_ui(self):
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        main_layout = self.layout()
        
        # 数据集配置
        dataset_group = QGroupBox("💾 数据集配置")
        dataset_group.setObjectName("configGroup")
        dataset_layout = QVBoxLayout()
        dataset_layout.setSpacing(10)
        dataset_layout.setContentsMargins(15, 20, 15, 15)
        dataset_layout.addWidget(QLabel("Repo ID:"))
        self.repo_id = QLineEdit(
            "local_user/lego_pick_place_so100_teleop_train"
        )
        self.repo_id.setObjectName("inputField")
        dataset_layout.addWidget(self.repo_id)
        dataset_layout.addWidget(QLabel("数据集根目录 (可选):"))
        dataset_root_layout = QHBoxLayout()
        dataset_root_layout.setSpacing(10)
        self.dataset_root = QLineEdit("")
        self.dataset_root.setObjectName("inputField")
        dataset_root_layout.addWidget(self.dataset_root)
        browse_btn = QPushButton("📁 浏览...")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self.browse_dataset_root)
        dataset_root_layout.addWidget(browse_btn)
        dataset_layout.addLayout(dataset_root_layout)
        self.push_to_hub = QCheckBox("推送到 Hub")
        dataset_layout.addWidget(self.push_to_hub)
        dataset_group.setLayout(dataset_layout)
        config_layout.addWidget(dataset_group)
        
        # 策略配置
        policy_group = QGroupBox("🧠 策略配置")
        policy_group.setObjectName("configGroup")
        policy_layout = QVBoxLayout()
        policy_layout.setSpacing(10)
        policy_layout.setContentsMargins(15, 20, 15, 15)
        policy_layout.addWidget(QLabel("策略类型:"))
        self.policy_type = QComboBox()
        self.policy_type.addItems(["act", "diffusion"])
        self.policy_type.setObjectName("comboBox")
        policy_layout.addWidget(self.policy_type)
        policy_layout.addWidget(QLabel("设备:"))
        self.device = QComboBox()
        self.device.addItems(["cuda", "cpu", "mps"])
        self.device.setObjectName("comboBox")
        policy_layout.addWidget(self.device)
        policy_group.setLayout(policy_layout)
        config_layout.addWidget(policy_group)
        
        # 输出配置
        output_group = QGroupBox("📤 输出配置")
        output_group.setObjectName("configGroup")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(10)
        output_layout.setContentsMargins(15, 20, 15, 15)
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir = QLineEdit(
            "outputs/train/lego_pick_place_so100_smolvla"
        )
        self.output_dir.setObjectName("inputField")
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(QLabel("任务名称:"))
        self.job_name = QLineEdit("lego_pick_place_so100_smolvla")
        self.job_name.setObjectName("inputField")
        output_layout.addWidget(self.job_name)
        self.wandb_enable = QCheckBox("启用 WandB")
        output_layout.addWidget(self.wandb_enable)
        output_group.setLayout(output_layout)
        config_layout.addWidget(output_group)

        # 继续训练
        resume_group = QGroupBox("🔄 继续训练")
        resume_group.setObjectName("configGroup")
        resume_layout = QVBoxLayout()
        resume_layout.setSpacing(10)
        resume_layout.setContentsMargins(15, 20, 15, 15)
        resume_layout.addWidget(QLabel("配置文件路径 (可选):"))
        config_path_layout = QHBoxLayout()
        config_path_layout.setSpacing(10)
        self.config_path = QLineEdit("")
        self.config_path.setObjectName("inputField")
        config_path_layout.addWidget(self.config_path)
        browse_config_btn = QPushButton("📁 浏览...")
        browse_config_btn.setObjectName("secondaryButton")
        browse_config_btn.clicked.connect(self.browse_config_path)
        config_path_layout.addWidget(browse_config_btn)
        resume_layout.addLayout(config_path_layout)
        self.resume = QCheckBox("从检查点恢复")
        resume_layout.addWidget(self.resume)
        resume_group.setLayout(resume_layout)
        config_layout.addWidget(resume_group)

        # 运行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        run_btn = QPushButton("🚀 开始训练")
        run_btn.setObjectName("actionButton")
        run_btn.clicked.connect(self.run_train)
        btn_layout.addWidget(run_btn)
        config_layout.addLayout(btn_layout)

        # 将配置布局插入到输出区域之前（索引0）
        main_layout.insertLayout(0, config_layout)
    
    def browse_dataset_root(self):
        path = QFileDialog.getExistingDirectory(self, "选择数据集根目录")
        if path:
            self.dataset_root.setText(path)

    def browse_config_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON Files (*.json)"
        )
        if path:
            self.config_path.setText(path)
    
    def run_train(self):
        cmd = [
            "python", "lerobot/scripts/train.py",
            f"--dataset.repo_id={self.repo_id.text()}",
            f"--policy.type={self.policy_type.currentText()}",
            f"--output_dir={self.output_dir.text()}",
            f"--job_name={self.job_name.text()}",
            f"--policy.device={self.device.currentText()}",
            f"--wandb.enable={str(self.wandb_enable.isChecked()).lower()}"
        ]

        if self.dataset_root.text():
            cmd.append(f"--dataset.root={self.dataset_root.text()}")

        if not self.push_to_hub.isChecked():
            cmd.append("--dataset.push_to_hub=false")

        if self.resume.isChecked() and self.config_path.text():
            cmd.extend([
                "--config_path", self.config_path.text(), "--resume=true"
            ])

        self.run_command(cmd)


class EvaluateWidget(BaseCommandWidget):
    """评估与回放模块"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_evaluate_ui()
    
    def setup_evaluate_ui(self):
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        main_layout = self.layout()
        
        # 评估模式选择
        mode_group = QGroupBox("🎯 模式")
        mode_group.setObjectName("configGroup")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        mode_layout.setContentsMargins(15, 20, 15, 15)
        self.eval_mode = QComboBox()
        self.eval_mode.addItems(["策略评估", "回放数据"])
        self.eval_mode.setObjectName("comboBox")
        self.eval_mode.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.eval_mode)
        mode_group.setLayout(mode_layout)
        config_layout.addWidget(mode_group)
        
        # 机器人配置
        robot_group = QGroupBox("🤖 机器人配置")
        robot_group.setObjectName("configGroup")
        robot_layout = QVBoxLayout()
        robot_layout.setSpacing(10)
        robot_layout.setContentsMargins(15, 20, 15, 15)
        robot_layout.addWidget(QLabel("端口:"))
        self.robot_port = QLineEdit("/dev/ttyACM1")
        self.robot_port.setObjectName("inputField")
        robot_layout.addWidget(self.robot_port)
        robot_layout.addWidget(QLabel("ID:"))
        self.robot_id = QLineEdit("blue")
        self.robot_id.setObjectName("inputField")
        robot_layout.addWidget(self.robot_id)
        robot_group.setLayout(robot_layout)
        config_layout.addWidget(robot_group)
        
        # 策略评估配置
        self.policy_group = QGroupBox("🧠 策略配置")
        self.policy_group.setObjectName("configGroup")
        policy_layout = QVBoxLayout()
        policy_layout.setSpacing(10)
        policy_layout.setContentsMargins(15, 20, 15, 15)
        policy_layout.addWidget(QLabel("策略路径:"))
        policy_path_layout = QHBoxLayout()
        policy_path_layout.setSpacing(10)
        self.policy_path = QLineEdit("")
        self.policy_path.setObjectName("inputField")
        policy_path_layout.addWidget(self.policy_path)
        browse_policy_btn = QPushButton("📁 浏览...")
        browse_policy_btn.setObjectName("secondaryButton")
        browse_policy_btn.clicked.connect(self.browse_policy_path)
        policy_path_layout.addWidget(browse_policy_btn)
        policy_layout.addLayout(policy_path_layout)
        self.policy_group.setLayout(policy_layout)
        config_layout.addWidget(self.policy_group)
        
        # 摄像头配置（仅评估模式）
        self.camera_group = QGroupBox("📷 摄像头配置")
        self.camera_group.setObjectName("configGroup")
        camera_layout = QVBoxLayout()
        camera_layout.setSpacing(10)
        camera_layout.setContentsMargins(15, 20, 15, 15)
        camera_layout.addWidget(QLabel("Top 摄像头索引:"))
        self.top_cam_idx = QLineEdit("0")
        self.top_cam_idx.setObjectName("inputField")
        camera_layout.addWidget(self.top_cam_idx)
        camera_layout.addWidget(QLabel("Gripper 摄像头索引:"))
        self.gripper_cam_idx = QLineEdit("2")
        self.gripper_cam_idx.setObjectName("inputField")
        camera_layout.addWidget(self.gripper_cam_idx)
        self.camera_group.setLayout(camera_layout)
        config_layout.addWidget(self.camera_group)
        
        # Teleop 配置（仅评估模式）
        self.teleop_group = QGroupBox("🎮 Teleop 配置")
        self.teleop_group.setObjectName("configGroup")
        teleop_layout = QVBoxLayout()
        teleop_layout.setSpacing(10)
        teleop_layout.setContentsMargins(15, 20, 15, 15)
        teleop_layout.addWidget(QLabel("端口:"))
        self.teleop_port = QLineEdit("/dev/ttyACM0")
        self.teleop_port.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_port)
        teleop_layout.addWidget(QLabel("ID:"))
        self.teleop_id = QLineEdit("yellow")
        self.teleop_id.setObjectName("inputField")
        teleop_layout.addWidget(self.teleop_id)
        self.teleop_group.setLayout(teleop_layout)
        config_layout.addWidget(self.teleop_group)
        
        # 数据集配置
        dataset_group = QGroupBox("💾 数据集配置")
        dataset_group.setObjectName("configGroup")
        dataset_layout = QVBoxLayout()
        dataset_layout.setSpacing(10)
        dataset_layout.setContentsMargins(15, 20, 15, 15)
        dataset_layout.addWidget(QLabel("Repo ID:"))
        self.repo_id = QLineEdit(
            "local_user/lego_pick_place_so100_teleop_train"
        )
        self.repo_id.setObjectName("inputField")
        dataset_layout.addWidget(self.repo_id)
        dataset_layout.addWidget(
            QLabel("Episode 数量 (评估) / Episode 索引 (回放):")
        )
        self.episode_num = QSpinBox()
        self.episode_num.setMinimum(0)
        self.episode_num.setValue(0)
        dataset_layout.addWidget(self.episode_num)
        dataset_layout.addWidget(QLabel("任务描述 (仅评估):"))
        self.task_desc = QLineEdit("Evaluation: pick and place")
        self.task_desc.setObjectName("inputField")
        dataset_layout.addWidget(self.task_desc)
        dataset_group.setLayout(dataset_layout)
        config_layout.addWidget(dataset_group)

        # 运行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        run_btn = QPushButton("▶️ 运行")
        run_btn.setObjectName("actionButton")
        run_btn.clicked.connect(self.run_evaluate)
        btn_layout.addWidget(run_btn)
        config_layout.addLayout(btn_layout)

        # 将配置布局插入到输出区域之前（索引0）
        main_layout.insertLayout(0, config_layout)

        self.on_mode_changed(0)
    
    def on_mode_changed(self, index):
        is_eval = index == 0
        self.policy_group.setVisible(is_eval)
        self.camera_group.setVisible(is_eval)
        self.teleop_group.setVisible(is_eval)
        if is_eval:
            self.episode_num.setMinimum(1)
            self.episode_num.setValue(10)
        else:
            self.episode_num.setMinimum(0)
            self.episode_num.setValue(0)
    
    def browse_policy_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择策略目录")
        if path:
            self.policy_path.setText(path)
    
    def run_evaluate(self):
        if self.eval_mode.currentIndex() == 0:  # 策略评估
            cameras_json = {
                "top": {
                    "type": "opencv",
                    "index_or_path": int(self.top_cam_idx.text()),
                    "fps": 30,
                    "width": 640,
                    "height": 360
                },
                "gripper": {
                    "type": "opencv",
                    "index_or_path": int(self.gripper_cam_idx.text()),
                    "fps": 30,
                    "width": 640,
                    "height": 360
                }
            }

            cmd = [
                "python", "-m", "lerobot.record",
                "--robot.type=so100_follower",
                f"--robot.port={self.robot_port.text()}",
                f"--robot.id={self.robot_id.text()}",
                f"--robot.cameras={json.dumps(cameras_json)}",
                "--teleop.type=so100_leader",
                f"--teleop.port={self.teleop_port.text()}",
                f"--teleop.id={self.teleop_id.text()}",
                "--display_data=false",
                f"--dataset.repo_id={self.repo_id.text()}",
                f"--dataset.num_episodes={self.episode_num.value()}",
                f"--dataset.single_task={self.task_desc.text()}",
                f"--policy.path={self.policy_path.text()}"
            ]
        else:  # 回放
            cmd = [
                "python", "-m", "lerobot.replay",
                "--robot.type=so100_follower",
                f"--robot.port={self.robot_port.text()}",
                f"--robot.id={self.robot_id.text()}",
                f"--dataset.repo_id={self.repo_id.text()}",
                f"--dataset.episode={self.episode_num.value()}"
            ]

        self.run_command(cmd)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 LeRobot SO100 GUI 工具")
        self.setGeometry(100, 100, 1200, 800)
        self.apply_stylesheet()
        
        # 创建标签页
        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        
        tabs.addTab(EnvironmentSetupWidget(), "📦 1. 环境准备")
        tabs.addTab(HardwareSetupWidget(), "⚙️ 2. 硬件连接与校准")
        tabs.addTab(TeleoperateWidget(), "🎮 3. 遥操作")
        tabs.addTab(RecordWidget(), "🎬 4. 数据录制")
        tabs.addTab(TrainWidget(), "🚀 5. 训练")
        tabs.addTab(EvaluateWidget(), "📊 6. 评估与回放")

        self.setCentralWidget(tabs)
    
    def apply_stylesheet(self):
        """应用现代化样式表"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTabWidget::pane {
            border: 1px solid #ddd;
            background-color: #ffffff;
            border-radius: 8px;
        }
        
        QTabBar::tab {
            background-color: #e8e8e8;
            color: #333;
            padding: 12px 24px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-size: 13px;
            font-weight: 500;
        }
        
        QTabBar::tab:selected {
            background-color: #4a90e2;
            color: white;
        }
        
        QTabBar::tab:hover {
            background-color: #d0d0d0;
        }
        
        QTabBar::tab:selected:hover {
            background-color: #357abd;
        }
        
        QGroupBox#configGroup {
            font-weight: 600;
            font-size: 14px;
            color: #2c3e50;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 15px;
            background-color: #fafafa;
        }
        
        QGroupBox#configGroup::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px;
            background-color: #fafafa;
        }
        
        QGroupBox#outputGroup {
            font-weight: 600;
            font-size: 14px;
            color: #2c3e50;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 15px;
            background-color: #fafafa;
        }
        
        QGroupBox#outputGroup::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px;
            background-color: #fafafa;
        }
        
        QLineEdit#inputField {
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: white;
            selection-background-color: #4a90e2;
        }
        
        QLineEdit#inputField:focus {
            border: 2px solid #4a90e2;
            background-color: #f8f9ff;
        }
        
        QLabel#infoLabel {
            background-color: #e3f2fd;
            border: 1px solid #90caf9;
            border-radius: 6px;
            padding: 12px 15px;
            font-size: 13px;
            color: #1565c0;
            margin: 10px 0;
        }
        
        QPushButton#primaryButton {
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
            min-width: 120px;
        }
        
        QPushButton#primaryButton:hover {
            background-color: #357abd;
        }
        
        QPushButton#primaryButton:pressed {
            background-color: #2a6ba0;
        }
        
        QPushButton#actionButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5cb85c, stop:1 #4a9d4a);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 30px;
            font-size: 14px;
            font-weight: 700;
            min-width: 150px;
        }
        
        QPushButton#actionButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a9d4a, stop:1 #3d8b3d);
        }
        
        QPushButton#actionButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3d8b3d, stop:1 #2e6a2e);
        }
        
        QPushButton#secondaryButton {
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton#secondaryButton:hover {
            background-color: #5a6268;
        }
        
        QPushButton#secondaryButton:pressed {
            background-color: #484f54;
        }
        
        QComboBox#comboBox {
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: white;
            min-width: 150px;
        }
        
        QComboBox#comboBox:hover {
            border: 2px solid #4a90e2;
        }
        
        QComboBox#comboBox:focus {
            border: 2px solid #4a90e2;
            background-color: #f8f9ff;
        }
        
        QComboBox#comboBox::drop-down {
            border: none;
            width: 30px;
        }
        
        QComboBox#comboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #666;
            width: 0;
            height: 0;
        }
        
        QSpinBox {
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: white;
        }
        
        QSpinBox:focus {
            border: 2px solid #4a90e2;
            background-color: #f8f9ff;
        }
        
        QCheckBox {
            font-size: 13px;
            color: #333;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        
        QCheckBox::indicator:hover {
            border: 2px solid #4a90e2;
        }
        
        QCheckBox::indicator:checked {
            background-color: #4a90e2;
            border: 2px solid #4a90e2;
        }
        
        QTextEdit#outputText {
            border: 2px solid #ddd;
            border-radius: 6px;
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            padding: 10px;
            selection-background-color: #264f78;
        }
        
        QLabel {
            color: #333;
            font-size: 13px;
            font-weight: 500;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        self.setStyleSheet(style)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
