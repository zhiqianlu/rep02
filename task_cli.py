#!/usr/bin/env python3
"""
计划任务命令行界面（Task Scheduler CLI）
支持通过命令行管理计划任务
"""
import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional

from task_scheduler import TaskScheduler, Task, TaskStatus, TaskPriority


def parse_datetime(dt_str: str) -> datetime:
    """解析日期时间字符串"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%H:%M:%S",
        "%H:%M"
    ]
    
    for fmt in formats:
        try:
            if fmt in ["%H:%M:%S", "%H:%M"]:
                # 只有时间，使用今天的日期
                today = datetime.now().date()
                time_part = datetime.strptime(dt_str, fmt).time()
                return datetime.combine(today, time_part)
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    # 尝试相对时间
    if dt_str.endswith('m'):
        minutes = int(dt_str[:-1])
        return datetime.now() + timedelta(minutes=minutes)
    elif dt_str.endswith('h'):
        hours = int(dt_str[:-1])
        return datetime.now() + timedelta(hours=hours)
    elif dt_str.endswith('d'):
        days = int(dt_str[:-1])
        return datetime.now() + timedelta(days=days)
    
    raise ValueError(f"无法解析日期时间: {dt_str}")


def parse_interval(interval_str: str) -> int:
    """解析时间间隔字符串，返回秒数"""
    if interval_str.endswith('s'):
        return int(interval_str[:-1])
    elif interval_str.endswith('m'):
        return int(interval_str[:-1]) * 60
    elif interval_str.endswith('h'):
        return int(interval_str[:-1]) * 3600
    elif interval_str.endswith('d'):
        return int(interval_str[:-1]) * 86400
    else:
        return int(interval_str)


def format_task(task: Task, verbose: bool = False) -> str:
    """格式化任务信息"""
    status_icons = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.RUNNING: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌",
        TaskStatus.CANCELLED: "🚫"
    }
    
    priority_colors = {
        TaskPriority.URGENT: "🔴",
        TaskPriority.HIGH: "🟠",
        TaskPriority.NORMAL: "🟢",
        TaskPriority.LOW: "⚪"
    }
    
    icon = status_icons.get(task.status, "❓")
    priority_icon = priority_colors.get(task.priority, "⚪")
    
    if verbose:
        lines = [
            f"{icon} [{task.task_id}] {task.name}",
            f"   {priority_icon} 优先级: {task.priority.name}",
            f"   📝 描述: {task.description or '无'}",
            f"   📅 计划时间: {task.scheduled_time}",
            f"   🔁 执行间隔: {task.interval_seconds or '一次性'}秒",
            f"   📊 状态: {task.status.value}",
            f"   🏃 执行次数: {task.run_count}",
            f"   🏷️  标签: {', '.join(task.tags) if task.tags else '无'}"
        ]
        if task.last_run:
            lines.append(f"   ⏰ 上次执行: {task.last_run}")
        if task.next_run:
            lines.append(f"   ⏰ 下次执行: {task.next_run}")
        return "\n".join(lines)
    else:
        return f"{icon} [{task.task_id}] {priority_icon} {task.name} - {task.status.value}"


def cmd_add(args, scheduler: TaskScheduler):
    """添加任务命令"""
    scheduled_time = None
    if args.time:
        scheduled_time = parse_datetime(args.time)
    
    interval = None
    if args.interval:
        interval = parse_interval(args.interval)
    
    priority = TaskPriority.NORMAL
    if args.priority:
        priority = TaskPriority[args.priority.upper()]
    
    tags = []
    if args.tags:
        tags = [t.strip() for t in args.tags.split(',')]
    
    task_id = scheduler.create_task(
        name=args.name,
        description=args.description or "",
        scheduled_time=scheduled_time,
        interval_seconds=interval,
        priority=priority,
        command=args.task_command or "",
        tags=tags,
        max_runs=args.max_runs
    )
    
    print(f"✅ 任务已创建: {args.name}")
    print(f"   任务ID: {task_id}")


def cmd_list(args, scheduler: TaskScheduler):
    """列出任务命令"""
    status = None
    if args.status:
        status = TaskStatus(args.status)
    
    priority = None
    if args.priority:
        priority = TaskPriority[args.priority.upper()]
    
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(',')]
    
    tasks = scheduler.list_tasks(status=status, priority=priority, tags=tags)
    
    if not tasks:
        print("📭 没有找到任务")
        return
    
    print(f"📋 任务列表 (共 {len(tasks)} 个):")
    print("-" * 50)
    for task in tasks:
        print(format_task(task, verbose=args.verbose))
        if args.verbose:
            print()


def cmd_show(args, scheduler: TaskScheduler):
    """显示任务详情命令"""
    task = scheduler.get_task(args.task_id)
    if task is None:
        print(f"❌ 任务不存在: {args.task_id}")
        return
    
    print(format_task(task, verbose=True))


def cmd_remove(args, scheduler: TaskScheduler):
    """删除任务命令"""
    task = scheduler.get_task(args.task_id)
    if task is None:
        print(f"❌ 任务不存在: {args.task_id}")
        return
    
    if not args.force:
        confirm = input(f"确定要删除任务 '{task.name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 已取消删除")
            return
    
    if scheduler.remove_task(args.task_id):
        print(f"✅ 任务已删除: {task.name}")
    else:
        print(f"❌ 删除任务失败")


def cmd_cancel(args, scheduler: TaskScheduler):
    """取消任务命令"""
    task = scheduler.get_task(args.task_id)
    if task is None:
        print(f"❌ 任务不存在: {args.task_id}")
        return
    
    if scheduler.cancel_task(args.task_id):
        print(f"🚫 任务已取消: {task.name}")
    else:
        print(f"❌ 取消任务失败")


def cmd_run(args, scheduler: TaskScheduler):
    """执行任务命令"""
    task = scheduler.get_task(args.task_id)
    if task is None:
        print(f"❌ 任务不存在: {args.task_id}")
        return
    
    print(f"🔄 开始执行任务: {task.name}")
    if scheduler.execute_task(args.task_id):
        print(f"✅ 任务执行完成")
    else:
        print(f"❌ 任务执行失败")


def cmd_update(args, scheduler: TaskScheduler):
    """更新任务命令"""
    task = scheduler.get_task(args.task_id)
    if task is None:
        print(f"❌ 任务不存在: {args.task_id}")
        return
    
    kwargs = {}
    
    if args.name:
        kwargs['name'] = args.name
    if args.description:
        kwargs['description'] = args.description
    if args.time:
        kwargs['scheduled_time'] = parse_datetime(args.time)
    if args.interval:
        kwargs['interval_seconds'] = parse_interval(args.interval)
    if args.priority:
        kwargs['priority'] = TaskPriority[args.priority.upper()]
    if args.task_command:
        kwargs['command'] = args.task_command
    if args.tags:
        kwargs['tags'] = [t.strip() for t in args.tags.split(',')]
    
    if not kwargs:
        print("⚠️  没有指定要更新的内容")
        return
    
    if scheduler.update_task(args.task_id, **kwargs):
        print(f"✅ 任务已更新: {task.name}")
    else:
        print(f"❌ 更新任务失败")


def cmd_stats(args, scheduler: TaskScheduler):
    """显示统计信息命令"""
    stats = scheduler.get_statistics()
    
    print("📊 任务统计")
    print("=" * 40)
    print(f"总任务数: {stats['total_tasks']}")
    print()
    print("按状态分类:")
    for status, count in stats['by_status'].items():
        print(f"  {status}: {count}")
    print()
    print("按优先级分类:")
    for priority, count in stats['by_priority'].items():
        print(f"  {priority}: {count}")


def cmd_start(args, scheduler: TaskScheduler):
    """启动调度器命令"""
    print(f"🚀 启动调度器，检查间隔: {args.interval}秒")
    print("按 Ctrl+C 停止...")
    
    try:
        scheduler.start(check_interval=args.interval)
        # 保持主线程运行
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  停止调度器...")
        scheduler.stop()
        print("✅ 调度器已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="计划任务调度器 - 命令行界面",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 添加一个新任务
  %(prog)s add "备份数据库" -d "每日备份" -t "1d" -i "1d" -p high

  # 列出所有任务
  %(prog)s list -v

  # 显示任务详情
  %(prog)s show abc123

  # 删除任务
  %(prog)s remove abc123

  # 启动调度器
  %(prog)s start --interval 60
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        default='tasks.json',
        help='任务存储文件路径 (默认: tasks.json)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加新任务')
    add_parser.add_argument('name', help='任务名称')
    add_parser.add_argument('-d', '--description', help='任务描述')
    add_parser.add_argument('-t', '--time', help='计划执行时间 (如: "2024-01-01 10:00" 或 "10m" 表示10分钟后)')
    add_parser.add_argument('-i', '--interval', help='重复间隔 (如: "30s", "5m", "1h", "1d")')
    add_parser.add_argument('-p', '--priority', choices=['low', 'normal', 'high', 'urgent'], help='优先级')
    add_parser.add_argument('-c', '--cmd', dest='task_command', help='要执行的命令')
    add_parser.add_argument('--tags', help='标签，逗号分隔')
    add_parser.add_argument('--max-runs', type=int, help='最大执行次数')
    add_parser.set_defaults(func=cmd_add)
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出任务')
    list_parser.add_argument('-s', '--status', choices=['pending', 'running', 'completed', 'failed', 'cancelled'], help='按状态筛选')
    list_parser.add_argument('-p', '--priority', choices=['low', 'normal', 'high', 'urgent'], help='按优先级筛选')
    list_parser.add_argument('--tags', help='按标签筛选，逗号分隔')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    list_parser.set_defaults(func=cmd_list)
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='显示任务详情')
    show_parser.add_argument('task_id', help='任务ID')
    show_parser.set_defaults(func=cmd_show)
    
    # remove 命令
    remove_parser = subparsers.add_parser('remove', help='删除任务')
    remove_parser.add_argument('task_id', help='任务ID')
    remove_parser.add_argument('-f', '--force', action='store_true', help='强制删除，不询问确认')
    remove_parser.set_defaults(func=cmd_remove)
    
    # cancel 命令
    cancel_parser = subparsers.add_parser('cancel', help='取消任务')
    cancel_parser.add_argument('task_id', help='任务ID')
    cancel_parser.set_defaults(func=cmd_cancel)
    
    # run 命令
    run_parser = subparsers.add_parser('run', help='立即执行任务')
    run_parser.add_argument('task_id', help='任务ID')
    run_parser.set_defaults(func=cmd_run)
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新任务')
    update_parser.add_argument('task_id', help='任务ID')
    update_parser.add_argument('-n', '--name', help='新的任务名称')
    update_parser.add_argument('-d', '--description', help='新的任务描述')
    update_parser.add_argument('-t', '--time', help='新的计划执行时间')
    update_parser.add_argument('-i', '--interval', help='新的重复间隔')
    update_parser.add_argument('-p', '--priority', choices=['low', 'normal', 'high', 'urgent'], help='新的优先级')
    update_parser.add_argument('-c', '--cmd', dest='task_command', help='新的命令')
    update_parser.add_argument('--tags', help='新的标签，逗号分隔')
    update_parser.set_defaults(func=cmd_update)
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.set_defaults(func=cmd_stats)
    
    # start 命令
    start_parser = subparsers.add_parser('start', help='启动调度器')
    start_parser.add_argument('--interval', type=int, default=60, help='检查间隔秒数 (默认: 60)')
    start_parser.set_defaults(func=cmd_start)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # 创建调度器实例
    scheduler = TaskScheduler(storage_file=args.file)
    
    # 执行命令
    args.func(args, scheduler)


if __name__ == "__main__":
    main()
