import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.logging.setup import get_logger

logger = get_logger("FileManagerTool")


class Tool(ABC):
    """Tool 基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 描述"""
        pass

    @property
    @abstractmethod
    def params_schema(self) -> Dict[str, Any]:
        """参数 Schema"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行 Tool"""
        pass


class FileManagerTool(Tool):
    """文件管理工具"""

    def __init__(self, root_dir: str = "workspace", max_file_size: int = 5242880):
        self.root_dir = os.path.abspath(root_dir)
        self.max_file_size = max_file_size
        self._ensure_root_dir()

    def _ensure_root_dir(self):
        """确保根目录存在"""
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir, exist_ok=True)
            logger.info(f"创建文件管理根目录: {self.root_dir}")

    @property
    def name(self) -> str:
        return "file_manager"

    @property
    def description(self) -> str:
        return "文件管理工具，可以查看、读取、创建/编辑文件"

    @property
    def params_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型：list(列出目录) / read(读取文件) / write(创建/编辑文件)",
                    "enum": ["list", "read", "write"],
                },
                "file_path": {
                    "type": "string",
                    "description": "文件路径（相对于根目录），如 'test.txt' 或 'subdir/file.txt'",
                },
                "content": {
                    "type": "string",
                    "description": "文件内容（action 为 write 时必填）",
                },
            },
            "required": ["action", "file_path"],
        }

    @property
    def prompt_hint(self) -> str:
        return """【重要】file_manager 工具参数规则：
- action: list（列出目录）、read（读取文件）、write（创建/编辑文件）
- file_path: 相对于根目录的路径，如 'test.txt'、'subdir/file.txt'
- content: write 时需要提供文件内容
- 根目录是 workspace/
"""

    def _validate_path(self, file_path: str) -> str:
        """验证路径是否在允许范围内
        
        Returns:
            绝对路径
            
        Raises:
            ValueError: 路径超出允许范围
        """
        if file_path is None:
            file_path = ""
        
        file_path = file_path.strip().replace("\\", "/")
        
        full_path = os.path.abspath(os.path.join(self.root_dir, file_path))
        
        if not full_path.startswith(self.root_dir):
            raise ValueError(f"路径 '{file_path}' 超出允许范围，只能在 '{self.root_dir}' 目录下操作")
        
        return full_path

    def _list_files(self, file_path: str) -> str:
        """列出目录内容"""
        target_path = self._validate_path(file_path)
        
        if not os.path.exists(target_path):
            return f"目录不存在: {file_path}"
        
        if not os.path.isdir(target_path):
            return f"不是目录: {file_path}"
        
        try:
            items = os.listdir(target_path)
            if not items:
                return f"目录为空: {file_path}"
            
            result = [f"目录: {file_path}", "-" * 40]
            for item in sorted(items):
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    result.append(f"  [DIR]  {item}/")
                else:
                    size = os.path.getsize(item_path)
                    result.append(f"  [FILE] {item} ({size} bytes)")
            
            return "\n".join(result)
        except PermissionError:
            return f"无权限访问: {file_path}"
        except Exception as e:
            return f"列出目录失败: {str(e)}"

    def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        target_path = self._validate_path(file_path)
        
        if not os.path.exists(target_path):
            return f"文件不存在: {file_path}"
        
        if not os.path.isfile(target_path):
            return f"不是文件: {file_path}"
        
        file_size = os.path.getsize(target_path)
        if file_size > self.max_file_size:
            return f"文件过大: {file_path} ({file_size} bytes)，最大支持 {self.max_file_size} bytes"
        
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return f"文件: {file_path}\n大小: {file_size} bytes\n{'-' * 40}\n{content}"
        except UnicodeDecodeError:
            return f"文件编码不支持，请使用 UTF-8 编码的文件: {file_path}"
        except PermissionError:
            return f"无权限读取: {file_path}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"

    def _write_file(self, file_path: str, content: str) -> str:
        """创建或编辑文件"""
        target_path = self._validate_path(file_path)
        
        parent_dir = os.path.dirname(target_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return f"文件写入成功: {file_path}"
        except PermissionError:
            return f"无权限写入: {file_path}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"

    def execute(self, **kwargs) -> str:
        """执行文件管理操作"""
        action = kwargs.get("action", "").lower()
        file_path = kwargs.get("file_path", "")
        content = kwargs.get("content", "")

        if not action:
            return "错误：未指定操作类型"

        if action not in ["list", "read", "write"]:
            return f"错误：不支持的操 '{action}'，支持的操作: list, read, write"

        if action == "list":
            return self._list_files(file_path)
        
        elif action == "read":
            return self._read_file(file_path)
        
        elif action == "write":
            if not content:
                return "错误：write 操作需要提供 content 参数"
            return self._write_file(file_path, content)
        
        return "错误：未知的操作"
