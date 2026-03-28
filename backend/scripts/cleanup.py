"""
数据清理脚本
清理过期数据和临时文件
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from app.core.database import AsyncSessionLocal
from app.models.crawler import CrawlTask
from app.models.user import UserActivity


async def cleanup_old_crawl_tasks(days: int = 30):
    """清理旧的爬虫任务记录"""
    async with AsyncSessionLocal() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = delete(CrawlTask).where(CrawlTask.created_at < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()
        
        print(f"✅ 清理了 {result.rowcount} 条爬虫任务记录")


async def cleanup_old_user_activities(days: int = 90):
    """清理旧的用户活动记录"""
    async with AsyncSessionLocal() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = delete(UserActivity).where(UserActivity.created_at < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()
        
        print(f"✅ 清理了 {result.rowcount} 条用户活动记录")


async def vacuum_database():
    """数据库VACUUM优化"""
    async with AsyncSessionLocal() as db:
        await db.execute("VACUUM")
        await db.commit()
        print("✅ 数据库VACUUM完成")


async def main():
    print("🗑️  开始清理数据...")
    print()
    
    # 清理爬虫任务（保留30天）
    await cleanup_old_crawl_tasks(days=30)
    
    # 清理用户活动（保留90天）
    await cleanup_old_user_activities(days=90)
    
    # 数据库优化
    await vacuum_database()
    
    print()
    print("✨ 数据清理完成！")


if __name__ == "__main__":
    asyncio.run(main())
