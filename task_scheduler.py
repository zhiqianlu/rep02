"""
计划任务调度器模块（Task Scheduler Module）
支持创建、管理和执行定时任务
"""
import json
import os
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """
    任务类，表示一个计划任务

    Attributes:
        name: 任务名称
        description: 任务描述
        scheduled_time: 计划执行时间
        interval_seconds: 重复执行间隔（秒），None 表示只执行一次
        priority: 任务优先级
        status: 任务状态
        task_id: 任务唯一标识
        created_at: 创建时间
        last_run: 上次执行时间
        next_run: 下次执行时间
        run_count: 执行次数
        max_runs: 最大执行次数，None 表示无限制
        command: 要执行的命令或脚本
        tags: 任务标签列表
    """
    name: str
    description: str = ""
    scheduled_time: Optional[datetime] = None
    interval_seconds: Optional[int] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    command: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if self.scheduled_time is None:
            self.scheduled_time = datetime.now()
        if self.next_run is None:
            self.next_run = self.scheduled_time

    def to_dict(self) -> Dict[str, Any]:
        """将任务转换为字典格式"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "interval_seconds": self.interval_seconds,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "max_runs": self.max_runs,
            "command": self.command,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典创建任务对象"""
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())[:16]),
            name=data["name"],
            description=data.get("description", ""),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]) if data.get("scheduled_time") else None,
            interval_seconds=data.get("interval_seconds"),
            priority=TaskPriority(data.get("priority", 2)),
            status=TaskStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            next_run=datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None,
            run_count=data.get("run_count", 0),
            max_runs=data.get("max_runs"),
            command=data.get("command", ""),
            tags=data.get("tags", [])
        )

    def is_due(self) -> bool:
        """检查任务是否到期需要执行"""
        if self.status not in [TaskStatus.PENDING, TaskStatus.COMPLETED]:
            return False
        if self.max_runs is not None and self.run_count >= self.max_runs:
            return False
        return self.next_run is not None and datetime.now() >= self.next_run

    def update_next_run(self):
        """更新下次执行时间"""
        if self.interval_seconds:
            self.next_run = datetime.now() + timedelta(seconds=self.interval_seconds)
            self.status = TaskStatus.PENDING
        else:
            self.next_run = None


class TaskScheduler:
    """
    任务调度器类

    支持添加、删除、查看和执行计划任务
    """

    def __init__(self, storage_file: str = "tasks.json"):
        """
        初始化任务调度器

        Args:
            storage_file: 任务存储文件路径
        """
        self.tasks: Dict[str, Task] = {}
        self.storage_file = storage_file
        self.running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._task_handlers: Dict[str, Callable] = {}
        self.load_tasks()

    def add_task(self, task: Task) -> str:
        """
        添加新任务

        Args:
            task: 要添加的任务

        Returns:
            任务ID
        """
        with self._lock:
            self.tasks[task.task_id] = task
            self.save_tasks()
            logger.info(f"任务已添加: {task.name} (ID: {task.task_id})")
            return task.task_id

    def create_task(
        self,
        name: str,
        description: str = "",
        scheduled_time: Optional[datetime] = None,
        interval_seconds: Optional[int] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        command: str = "",
        tags: Optional[List[str]] = None,
        max_runs: Optional[int] = None
    ) -> str:
        """
        创建并添加新任务

        Args:
            name: 任务名称
            description: 任务描述
            scheduled_time: 计划执行时间
            interval_seconds: 重复执行间隔
            priority: 任务优先级
            command: 要执行的命令
            tags: 任务标签
            max_runs: 最大执行次数

        Returns:
            任务ID
        """
        task = Task(
            name=name,
            description=description,
            scheduled_time=scheduled_time or datetime.now(),
            interval_seconds=interval_seconds,
            priority=priority,
            command=command,
            tags=tags or [],
            max_runs=max_runs
        )
        return self.add_task(task)

    def remove_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks.pop(task_id)
                self.save_tasks()
                logger.info(f"任务已删除: {task.name} (ID: {task_id})")
                return True
            logger.warning(f"任务不存在: {task_id}")
            return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象或 None
        """
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        tags: Optional[List[str]] = None
    ) -> List[Task]:
        """
        列出任务

        Args:
            status: 按状态筛选
            priority: 按优先级筛选
            tags: 按标签筛选

        Returns:
            符合条件的任务列表
        """
        result = list(self.tasks.values())

        if status is not None:
            result = [t for t in result if t.status == status]

        if priority is not None:
            result = [t for t in result if t.priority == priority]

        if tags:
            result = [t for t in result if any(tag in t.tags for tag in tags)]

        # 按优先级和计划时间排序
        result.sort(key=lambda t: (-t.priority.value, t.next_run or datetime.max))
        return result

    def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        interval_seconds: Optional[int] = None,
        priority: Optional[TaskPriority] = None,
        command: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[TaskStatus] = None
    ) -> bool:
        """
        更新任务

        Args:
            task_id: 任务ID
            其他参数: 要更新的字段

        Returns:
            是否更新成功
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if task is None:
                logger.warning(f"任务不存在: {task_id}")
                return False

            if name is not None:
                task.name = name
            if description is not None:
                task.description = description
            if scheduled_time is not None:
                task.scheduled_time = scheduled_time
                task.next_run = scheduled_time
            if interval_seconds is not None:
                task.interval_seconds = interval_seconds
            if priority is not None:
                task.priority = priority
            if command is not None:
                task.command = command
            if tags is not None:
                task.tags = tags
            if status is not None:
                task.status = status

            self.save_tasks()
            logger.info(f"任务已更新: {task.name} (ID: {task_id})")
            return True

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        return self.update_task(task_id, status=TaskStatus.CANCELLED)

    def execute_task(self, task_id: str, handler: Optional[Callable] = None) -> bool:
        """
        执行任务

        Args:
            task_id: 任务ID
            handler: 任务执行处理函数

        Returns:
            是否执行成功
        """
        task = self.get_task(task_id)
        if task is None:
            logger.warning(f"任务不存在: {task_id}")
            return False

        if task.status == TaskStatus.CANCELLED:
            logger.warning(f"任务已取消，无法执行: {task_id}")
            return False

        try:
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()
            logger.info(f"开始执行任务: {task.name} (ID: {task_id})")

            # 执行任务
            if handler:
                handler(task)
            elif task.task_id in self._task_handlers:
                self._task_handlers[task.task_id](task)
            elif task.command:
                # 执行命令（简单示例，实际应用中需要更安全的处理）
                logger.info("执行任务命令")
            else:
                logger.info(f"任务 {task.name} 没有定义执行内容")

            task.run_count += 1
            task.status = TaskStatus.COMPLETED
            task.update_next_run()
            self.save_tasks()
            logger.info(f"任务执行完成: {task.name} (ID: {task_id})")
            return True

        except Exception as e:
            task.status = TaskStatus.FAILED
            self.save_tasks()
            logger.error(f"任务执行失败: {task.name} (ID: {task_id}), 错误: {e}")
            return False

    def register_handler(self, task_id: str, handler: Callable[[Task], None]):
        """
        为任务注册执行处理函数

        Args:
            task_id: 任务ID
            handler: 处理函数
        """
        self._task_handlers[task_id] = handler
        logger.info(f"已为任务 {task_id} 注册处理函数")

    def save_tasks(self):
        """保存任务到文件"""
        try:
            data = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"任务已保存到 {self.storage_file}")
        except Exception as e:
            logger.error(f"保存任务失败: {e}")

    def load_tasks(self):
        """从文件加载任务"""
        if not os.path.exists(self.storage_file):
            logger.info(f"任务文件不存在，将创建新文件: {self.storage_file}")
            return

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.tasks = {task_id: Task.from_dict(task_data) for task_id, task_data in data.items()}
            logger.info(f"已加载 {len(self.tasks)} 个任务")
        except Exception as e:
            logger.error(f"加载任务失败: {e}")

    def get_due_tasks(self) -> List[Task]:
        """获取所有到期需要执行的任务"""
        return [task for task in self.tasks.values() if task.is_due()]

    def start(self, check_interval: int = 60):
        """
        启动调度器

        Args:
            check_interval: 检查间隔（秒）
        """
        if self.running:
            logger.warning("调度器已在运行中")
            return

        self.running = True
        self._scheduler_thread = threading.Thread(
            target=self._run_scheduler,
            args=(check_interval,),
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info(f"调度器已启动，检查间隔: {check_interval}秒")

    def stop(self):
        """停止调度器"""
        self.running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("调度器已停止")

    def _run_scheduler(self, check_interval: int):
        """调度器主循环"""
        while self.running:
            try:
                due_tasks = self.get_due_tasks()
                for task in due_tasks:
                    self.execute_task(task.task_id)
            except Exception as e:
                logger.error(f"调度器错误: {e}")

            time.sleep(check_interval)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息字典
        """
        total = len(self.tasks)
        status_counts = {}
        priority_counts = {}

        for task in self.tasks.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
            priority_counts[task.priority.name] = priority_counts.get(task.priority.name, 0) + 1

        return {
            "total_tasks": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "pending_count": status_counts.get(TaskStatus.PENDING.value, 0),
            "completed_count": status_counts.get(TaskStatus.COMPLETED.value, 0),
            "failed_count": status_counts.get(TaskStatus.FAILED.value, 0)
        }


def demo():
    """演示任务调度器功能"""
    print("=" * 50)
    print("计划任务调度器演示")
    print("=" * 50)

    # 创建调度器实例
    scheduler = TaskScheduler(storage_file="demo_tasks.json")

    # 创建一些示例任务
    task1_id = scheduler.create_task(
        name="数据备份",
        description="每日自动备份数据库",
        scheduled_time=datetime.now() + timedelta(seconds=5),
        interval_seconds=86400,  # 每天执行
        priority=TaskPriority.HIGH,
        tags=["备份", "数据库"]
    )

    task2_id = scheduler.create_task(
        name="发送报告",
        description="每周发送工作报告",
        scheduled_time=datetime.now() + timedelta(seconds=10),
        interval_seconds=604800,  # 每周执行
        priority=TaskPriority.NORMAL,
        tags=["报告", "邮件"]
    )

    task3_id = scheduler.create_task(
        name="清理临时文件",
        description="清理系统临时文件",
        scheduled_time=datetime.now() + timedelta(seconds=15),
        priority=TaskPriority.LOW,
        tags=["清理", "系统"]
    )

    # 列出所有任务
    print("\n所有任务:")
    print("-" * 50)
    for task in scheduler.list_tasks():
        print(f"[{task.task_id}] {task.name}")
        print(f"    描述: {task.description}")
        print(f"    优先级: {task.priority.name}")
        print(f"    状态: {task.status.value}")
        print(f"    计划时间: {task.scheduled_time}")
        print(f"    标签: {', '.join(task.tags)}")
        print()

    # 显示统计信息
    print("任务统计:")
    print("-" * 50)
    stats = scheduler.get_statistics()
    print(f"总任务数: {stats['total_tasks']}")
    print(f"待执行: {stats['pending_count']}")
    print(f"已完成: {stats['completed_count']}")
    print(f"失败: {stats['failed_count']}")

    # 手动执行一个任务
    print("\n手动执行任务:")
    print("-" * 50)
    scheduler.execute_task(task1_id)

    # 清理演示文件
    if os.path.exists("demo_tasks.json"):
        os.remove("demo_tasks.json")

    print("\n演示完成!")


if __name__ == "__main__":
    demo()
