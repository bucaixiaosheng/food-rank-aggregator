"""
餐厅和菜系模型
"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Cuisine(Base):
    """
    菜系分类模型
    """
    __tablename__ = "cuisines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="菜系名称")
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="父级菜系ID")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="菜系描述")
    icon: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="图标emoji")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<Cuisine {self.name}>"


class Restaurant(Base):
    """
    餐厅模型
    """
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="餐厅名称")
    address: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="详细地址")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True, comment="纬度")
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True, comment="经度")
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="电话")
    cuisine_type: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="菜系类型")
    price_range: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="价格区间，如：¥¥¥")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, comment="综合评分")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="餐厅描述")
    business_hours: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="营业时间")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="主图URL")
    
    # 平台来源信息
    platform_source: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="数据来源平台")
    platform_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="平台餐厅ID")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    platform_ratings = relationship("PlatformRating", back_populates="restaurant", lazy="dynamic")
    notes = relationship("Note", back_populates="restaurant", lazy="dynamic")

    def __repr__(self):
        return f"<Restaurant {self.name}>"
