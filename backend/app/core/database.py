"""
数据库连接配置
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 创建基类
Base = declarative_base()


# 数据库会话依赖
async def get_db() -> AsyncSession:
    """
    获取数据库会话
    用于FastAPI依赖注入
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库
    创建所有表
    """
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.models import restaurant, user, social, crawler  # noqa
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
