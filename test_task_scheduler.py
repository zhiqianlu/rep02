"""
计划任务调度器单元测试
"""
import os
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import tempfile

from task_scheduler import (
    Task,
    TaskScheduler,
    TaskStatus,
    TaskPriority
)


class TestTask(unittest.TestCase):
    """Task 类测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(name="测试任务", description="这是一个测试任务")
        
        self.assertEqual(task.name, "测试任务")
        self.assertEqual(task.description, "这是一个测试任务")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.NORMAL)
        self.assertEqual(task.run_count, 0)
        self.assertIsNotNone(task.task_id)
        self.assertIsNotNone(task.created_at)

    def test_task_to_dict(self):
        """测试任务转换为字典"""
        task = Task(
            name="测试任务",
            description="描述",
            priority=TaskPriority.HIGH,
            tags=["标签1", "标签2"]
        )
        
        data = task.to_dict()
        
        self.assertEqual(data["name"], "测试任务")
        self.assertEqual(data["description"], "描述")
        self.assertEqual(data["priority"], TaskPriority.HIGH.value)
        self.assertEqual(data["tags"], ["标签1", "标签2"])
        self.assertEqual(data["status"], TaskStatus.PENDING.value)

    def test_task_from_dict(self):
        """测试从字典创建任务"""
        data = {
            "task_id": "test123",
            "name": "测试任务",
            "description": "描述",
            "scheduled_time": "2024-01-01T10:00:00",
            "interval_seconds": 3600,
            "priority": 3,
            "status": "pending",
            "created_at": "2024-01-01T09:00:00",
            "run_count": 5,
            "tags": ["测试"]
        }
        
        task = Task.from_dict(data)
        
        self.assertEqual(task.task_id, "test123")
        self.assertEqual(task.name, "测试任务")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.interval_seconds, 3600)
        self.assertEqual(task.run_count, 5)

    def test_task_is_due(self):
        """测试任务是否到期"""
        # 过去的时间，应该到期
        past_task = Task(
            name="过期任务",
            scheduled_time=datetime.now() - timedelta(hours=1)
        )
        self.assertTrue(past_task.is_due())
        
        # 未来的时间，不应该到期
        future_task = Task(
            name="未来任务",
            scheduled_time=datetime.now() + timedelta(hours=1)
        )
        self.assertFalse(future_task.is_due())
        
        # 已取消的任务不应该到期
        cancelled_task = Task(
            name="已取消任务",
            scheduled_time=datetime.now() - timedelta(hours=1),
            status=TaskStatus.CANCELLED
        )
        self.assertFalse(cancelled_task.is_due())

    def test_task_max_runs(self):
        """测试最大执行次数限制"""
        task = Task(
            name="限次任务",
            scheduled_time=datetime.now() - timedelta(hours=1),
            max_runs=3,
            run_count=3
        )
        self.assertFalse(task.is_due())
        
        task.run_count = 2
        self.assertTrue(task.is_due())

    def test_task_update_next_run(self):
        """测试更新下次执行时间"""
        task = Task(
            name="重复任务",
            interval_seconds=3600
        )
        
        task.update_next_run()
        
        self.assertIsNotNone(task.next_run)
        self.assertEqual(task.status, TaskStatus.PENDING)


class TestTaskScheduler(unittest.TestCase):
    """TaskScheduler 类测试"""

    def setUp(self):
        """测试前准备"""
        # 使用临时文件作为存储
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        self.temp_file.close()
        self.scheduler = TaskScheduler(storage_file=self.temp_file.name)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_create_task(self):
        """测试创建任务"""
        task_id = self.scheduler.create_task(
            name="测试任务",
            description="这是一个测试任务",
            priority=TaskPriority.HIGH
        )
        
        self.assertIsNotNone(task_id)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.name, "测试任务")
        self.assertEqual(task.priority, TaskPriority.HIGH)

    def test_add_task(self):
        """测试添加任务"""
        task = Task(name="新任务", description="新任务描述")
        task_id = self.scheduler.add_task(task)
        
        self.assertEqual(task_id, task.task_id)
        self.assertEqual(len(self.scheduler.tasks), 1)

    def test_remove_task(self):
        """测试删除任务"""
        task_id = self.scheduler.create_task(name="待删除任务")
        
        result = self.scheduler.remove_task(task_id)
        
        self.assertTrue(result)
        self.assertIsNone(self.scheduler.get_task(task_id))

    def test_remove_nonexistent_task(self):
        """测试删除不存在的任务"""
        result = self.scheduler.remove_task("nonexistent")
        self.assertFalse(result)

    def test_list_tasks(self):
        """测试列出任务"""
        self.scheduler.create_task(name="任务1", priority=TaskPriority.HIGH)
        self.scheduler.create_task(name="任务2", priority=TaskPriority.LOW)
        self.scheduler.create_task(name="任务3", priority=TaskPriority.NORMAL)
        
        tasks = self.scheduler.list_tasks()
        
        self.assertEqual(len(tasks), 3)
        # 应该按优先级排序，高优先级在前
        self.assertEqual(tasks[0].priority, TaskPriority.HIGH)

    def test_list_tasks_by_status(self):
        """测试按状态筛选任务"""
        task1_id = self.scheduler.create_task(name="待执行任务")
        task2_id = self.scheduler.create_task(name="已完成任务")
        
        self.scheduler.update_task(task2_id, status=TaskStatus.COMPLETED)
        
        pending_tasks = self.scheduler.list_tasks(status=TaskStatus.PENDING)
        completed_tasks = self.scheduler.list_tasks(status=TaskStatus.COMPLETED)
        
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(len(completed_tasks), 1)

    def test_list_tasks_by_tags(self):
        """测试按标签筛选任务"""
        self.scheduler.create_task(name="任务1", tags=["备份", "数据库"])
        self.scheduler.create_task(name="任务2", tags=["清理"])
        self.scheduler.create_task(name="任务3", tags=["备份", "文件"])
        
        backup_tasks = self.scheduler.list_tasks(tags=["备份"])
        
        self.assertEqual(len(backup_tasks), 2)

    def test_update_task(self):
        """测试更新任务"""
        task_id = self.scheduler.create_task(
            name="原名称",
            description="原描述",
            priority=TaskPriority.NORMAL
        )
        
        result = self.scheduler.update_task(
            task_id,
            name="新名称",
            priority=TaskPriority.HIGH
        )
        
        self.assertTrue(result)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.name, "新名称")
        self.assertEqual(task.priority, TaskPriority.HIGH)

    def test_cancel_task(self):
        """测试取消任务"""
        task_id = self.scheduler.create_task(name="待取消任务")
        
        result = self.scheduler.cancel_task(task_id)
        
        self.assertTrue(result)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.CANCELLED)

    def test_execute_task(self):
        """测试执行任务"""
        task_id = self.scheduler.create_task(
            name="待执行任务",
            scheduled_time=datetime.now() - timedelta(hours=1)
        )
        
        result = self.scheduler.execute_task(task_id)
        
        self.assertTrue(result)
        task = self.scheduler.get_task(task_id)
        self.assertEqual(task.run_count, 1)
        self.assertIsNotNone(task.last_run)

    def test_execute_task_with_handler(self):
        """测试使用处理函数执行任务"""
        task_id = self.scheduler.create_task(name="有处理函数的任务")
        
        handler_called = [False]
        def test_handler(task):
            handler_called[0] = True
        
        result = self.scheduler.execute_task(task_id, handler=test_handler)
        
        self.assertTrue(result)
        self.assertTrue(handler_called[0])

    def test_execute_cancelled_task(self):
        """测试执行已取消的任务"""
        task_id = self.scheduler.create_task(name="已取消任务")
        self.scheduler.cancel_task(task_id)
        
        result = self.scheduler.execute_task(task_id)
        
        self.assertFalse(result)

    def test_register_handler(self):
        """测试注册处理函数"""
        task_id = self.scheduler.create_task(name="有注册处理函数的任务")
        
        handler_called = [False]
        def test_handler(task):
            handler_called[0] = True
        
        self.scheduler.register_handler(task_id, test_handler)
        self.scheduler.execute_task(task_id)
        
        self.assertTrue(handler_called[0])

    def test_save_and_load_tasks(self):
        """测试保存和加载任务"""
        self.scheduler.create_task(
            name="持久化任务",
            description="这个任务会被保存",
            priority=TaskPriority.HIGH,
            tags=["测试"]
        )
        
        # 创建新的调度器实例，加载之前保存的任务
        new_scheduler = TaskScheduler(storage_file=self.temp_file.name)
        
        self.assertEqual(len(new_scheduler.tasks), 1)
        task = list(new_scheduler.tasks.values())[0]
        self.assertEqual(task.name, "持久化任务")
        self.assertEqual(task.priority, TaskPriority.HIGH)

    def test_get_due_tasks(self):
        """测试获取到期任务"""
        # 创建一个过期任务
        self.scheduler.create_task(
            name="过期任务",
            scheduled_time=datetime.now() - timedelta(hours=1)
        )
        
        # 创建一个未到期任务
        self.scheduler.create_task(
            name="未到期任务",
            scheduled_time=datetime.now() + timedelta(hours=1)
        )
        
        due_tasks = self.scheduler.get_due_tasks()
        
        self.assertEqual(len(due_tasks), 1)
        self.assertEqual(due_tasks[0].name, "过期任务")

    def test_get_statistics(self):
        """测试获取统计信息"""
        task1_id = self.scheduler.create_task(name="任务1", priority=TaskPriority.HIGH)
        task2_id = self.scheduler.create_task(name="任务2", priority=TaskPriority.LOW)
        task3_id = self.scheduler.create_task(name="任务3", priority=TaskPriority.HIGH)
        
        self.scheduler.execute_task(task1_id)
        self.scheduler.cancel_task(task2_id)
        
        stats = self.scheduler.get_statistics()
        
        self.assertEqual(stats['total_tasks'], 3)
        self.assertEqual(stats['completed_count'], 1)
        self.assertEqual(stats['by_priority']['HIGH'], 2)

    def test_repeating_task(self):
        """测试重复执行任务"""
        task_id = self.scheduler.create_task(
            name="重复任务",
            scheduled_time=datetime.now() - timedelta(hours=1),
            interval_seconds=3600
        )
        
        # 第一次执行
        self.scheduler.execute_task(task_id)
        task = self.scheduler.get_task(task_id)
        
        self.assertEqual(task.run_count, 1)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNotNone(task.next_run)


class TestTaskSchedulerThreading(unittest.TestCase):
    """TaskScheduler 线程相关测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        self.temp_file.close()
        self.scheduler = TaskScheduler(storage_file=self.temp_file.name)

    def tearDown(self):
        """测试后清理"""
        if self.scheduler.running:
            self.scheduler.stop()
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_start_and_stop(self):
        """测试启动和停止调度器"""
        self.scheduler.start(check_interval=1)
        
        self.assertTrue(self.scheduler.running)
        self.assertIsNotNone(self.scheduler._scheduler_thread)
        
        self.scheduler.stop()
        
        self.assertFalse(self.scheduler.running)


if __name__ == '__main__':
    unittest.main()
