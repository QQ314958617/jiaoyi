"""
Asciicast - 终端录制
基于 Claude Code asciicast.ts 设计

录制终端会话为asciicast格式。
"""
import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RecordingState:
    """录制状态"""
    file_path: Optional[str] = None
    timestamp: int = 0


# 全局录制状态
_recording_state = RecordingState()


def get_record_file_path(
    session_id: str,
    original_cwd: str,
    config_dir: str,
    env_var: str = "CLAUDE_CODE_TERMINAL_RECORDING",
) -> Optional[str]:
    """
    获取录制文件路径
    
    Args:
        session_id: 会话ID
        original_cwd: 原始工作目录
        config_dir: 配置目录
        env_var: 环境变量名
        
    Returns:
        录制文件路径或None
    """
    global _recording_state
    
    if _recording_state.file_path is not None:
        return _recording_state.file_path
    
    # 检查是否启用
    recording_enabled = os.environ.get(env_var, '').lower()
    if recording_enabled not in ('1', 'true', 'yes'):
        return None
    
    # 计算路径
    projects_dir = os.path.join(config_dir, 'projects')
    from .path_utils import sanitize_path
    project_dir = os.path.join(projects_dir, sanitize_path(original_cwd))
    
    _recording_state.timestamp = int(time.time() * 1000)
    _recording_state.file_path = os.path.join(
        project_dir,
        f"{session_id}-{_recording_state.timestamp}.cast"
    )
    
    return _recording_state.file_path


def reset_recording_state() -> None:
    """重置录制状态（测试用）"""
    global _recording_state
    _recording_state = RecordingState()


def get_session_recording_paths(
    session_id: str,
    original_cwd: str,
    config_dir: str,
) -> List[str]:
    """
    获取当前会话的所有录制文件
    
    Args:
        session_id: 会话ID
        original_cwd: 原始工作目录
        config_dir: 配置目录
        
    Returns:
        录制文件路径列表
    """
    projects_dir = os.path.join(config_dir, 'projects')
    from .path_utils import sanitize_path
    project_dir = os.path.join(projects_dir, sanitize_path(original_cwd))
    
    if not os.path.isdir(project_dir):
        return []
    
    files = []
    for f in os.listdir(project_dir):
        if f.startswith(session_id) and f.endswith('.cast'):
            files.append(os.path.join(project_dir, f))
    
    return sorted(files)


class AsciicastWriter:
    """
    Asciicast录制写入器
    
    用于将终端会话写入asciicast格式文件。
    """
    
    HEADER = {
        "version": 2,
        "width": 80,
        "height": 24,
    }
    
    def __init__(
        self,
        file_path: str,
        width: int = 80,
        height: int = 24,
    ):
        """
        Args:
            file_path: 录制文件路径
            width: 终端宽度
            height: 终端高度
        """
        self.file_path = file_path
        self.header = {
            "version": 2,
            "width": width,
            "height": height,
        }
        self._start_time = time.time()
        self._file = None
    
    def start(self) -> None:
        """开始录制"""
        import os
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self._file = open(self.file_path, 'w')
        self._file.write(json.dumps(self.header) + '\n')
    
    def write(
        self,
        data: str,
        event_type: str = "o",  # "o"=stdout, "i"=stdin
    ) -> None:
        """
        写入录制数据
        
        Args:
            data: 数据内容
            event_type: 事件类型
        """
        if not self._file:
            return
        
        # 计算相对时间
        delay = time.time() - self._start_time
        
        # asciicast格式: [timestamp, event_type, data]
        line = json.dumps([round(delay, 6), event_type, data])
        self._file.write(line + '\n')
    
    def close(self) -> None:
        """关闭录制"""
        if self._file:
            self._file.close()
            self._file = None
    
    def __enter__(self) -> "AsciicastWriter":
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# 导出
__all__ = [
    "RecordingState",
    "get_record_file_path",
    "reset_recording_state",
    "get_session_recording_paths",
    "AsciicastWriter",
]
