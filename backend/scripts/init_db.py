#!/usr/bin/env python3
"""
数据库初始化脚本
创建表并插入种子数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, async_session_maker, Base
from app.models import (
    Cuisine, Restaurant, User, TasteProfile, UserActivity,
    Note, Comment, Follow, Favorite, CrawlTask, PlatformRating, Ranking, Blacklist
)


async def create_tables():
    """创建所有表"""
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.models import restaurant, user, social, crawler  # noqa
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print("✓ 数据库表创建完成")


async def insert_seed_data():
    """插入种子数据"""
    async with async_session_maker() as session:
        try:
            # 1. 插入菜系数据（20+）
            cuisines_data = [
                # 中式菜系
                {"name": "川菜", "description": "麻辣鲜香，口味浓郁", "icon": "🌶️"},
                {"name": "粤菜", "description": "清淡鲜美，注重原味", "icon": "🥢"},
                {"name": "湘菜", "description": "香辣浓烈，重油重色", "icon": "🔥"},
                {"name": "鲁菜", "description": "咸鲜为主，善用爆炒", "icon": "🍖"},
                {"name": "苏菜", "description": "口味清淡，注重造型", "icon": "🦐"},
                {"name": "浙菜", "description": "清香爽脆，选料讲究", "icon": "🐟"},
                {"name": "闽菜", "description": "清鲜淡爽，善用海鲜", "icon": "🦀"},
                {"name": "徽菜", "description": "重油重色，朴实醇厚", "icon": "🥘"},
                {"name": "京菜", "description": "宫廷菜系，口味醇厚", "icon": "🦆"},
                {"name": "东北菜", "description": "量大实惠，口味浓重", "icon": "🥟"},
                {"name": "西北菜", "description": "粗犷豪放，面食为主", "icon": "🍜"},
                {"name": "云南菜", "description": "酸辣开胃，食材丰富", "icon": "🍄"},
                {"name": "贵州菜", "description": "酸辣鲜香，口味独特", "icon": "🍲"},
                
                # 国际菜系
                {"name": "日料", "description": "精致清淡，注重食材", "icon": "🍣"},
                {"name": "韩餐", "description": "辛辣酸甜，泡菜为主", "icon": "🥬"},
                {"name": "西餐", "description": "浪漫精致，牛排意面", "icon": "🥩"},
                {"name": "泰餐", "description": "酸辣甜咸，香料丰富", "icon": "🥥"},
                {"name": "印度菜", "description": "浓郁咖喱，香料王国", "icon": "🍛"},
                {"name": "越南菜", "description": "清淡健康，法式融合", "icon": "🍜"},
                {"name": "新加坡菜", "description": "多元融合，南洋风味", "icon": "🦐"},
                {"name": "墨西哥菜", "description": "热情奔放，玉米为主", "icon": "🌮"},
            ]
            
            cuisines = [Cuisine(**data) for data in cuisines_data]
            session.add_all(cuisines)
            print(f"✓ 插入 {len(cuisines)} 个菜系")
            
            # 2. 插入示例用户（2个）
            users_data = [
                {
                    "nickname": "美食家小王",
                    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=wang",
                    "bio": "资深吃货，热爱探索各种美食",
                },
                {
                    "nickname": "吃货小李",
                    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=li",
                    "bio": "喜欢分享美食体验的美食博主",
                },
            ]
            
            users = [User(**data) for data in users_data]
            session.add_all(users)
            await session.flush()  # 获取用户ID
            
            # 3. 插入口味画像
            taste_profiles_data = [
                {
                    "user_id": users[0].id,
                    "preferred_cuisines": ["川菜", "湘菜", "火锅"],
                    "preferred_price_range": "¥¥-¥¥¥",
                    "preferred_spice_level": 4,
                    "flavor_tags": ["麻辣", "鲜香", "刺激"],
                    "dietary_restrictions": [],
                },
                {
                    "user_id": users[1].id,
                    "preferred_cuisines": ["粤菜", "日料", "西餐"],
                    "preferred_price_range": "¥¥¥-¥¥¥¥",
                    "preferred_spice_level": 2,
                    "flavor_tags": ["清淡", "精致", "健康"],
                    "dietary_restrictions": ["海鲜过敏"],
                },
            ]
            
            taste_profiles = [TasteProfile(**data) for data in taste_profiles_data]
            session.add_all(taste_profiles)
            print(f"✓ 插入 {len(users)} 个用户和口味画像")
            
            # 4. 插入示例餐厅（10家）
            restaurants_data = [
                {
                    "name": "老成都川菜馆",
                    "address": "朝阳区三里屯太古里北区B1层",
                    "latitude": 39.9342,
                    "longitude": 116.4535,
                    "phone": "010-64176688",
                    "cuisine_type": "川菜",
                    "price_range": "¥¥",
                    "rating": 4.5,
                    "description": "正宗川菜，麻婆豆腐、水煮鱼必点",
                    "business_hours": "11:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400",
                    "platform_source": "大众点评",
                    "platform_id": "dianping_123456",
                },
                {
                    "name": "鼎泰丰",
                    "address": "朝阳区建国门外大街1号国贸商城",
                    "latitude": 39.9087,
                    "longitude": 116.4609,
                    "phone": "010-65051233",
                    "cuisine_type": "台湾菜",
                    "price_range": "¥¥¥",
                    "rating": 4.7,
                    "description": "米其林一星，小笼包享誉全球",
                    "business_hours": "11:00-21:30",
                    "image_url": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=400",
                    "platform_source": "大众点评",
                    "platform_id": "dianping_234567",
                },
                {
                    "name": "海底捞火锅",
                    "address": "海淀区中关村大街15号",
                    "latitude": 39.9837,
                    "longitude": 116.3189,
                    "phone": "010-82628866",
                    "cuisine_type": "火锅",
                    "price_range": "¥¥¥",
                    "rating": 4.8,
                    "description": "服务至上，火锅界标杆",
                    "business_hours": "10:00-次日02:00",
                    "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400",
                    "platform_source": "大众点评",
                    "platform_id": "dianping_345678",
                },
                {
                    "name": "大董烤鸭店",
                    "address": "东城区东四十条甲22号",
                    "latitude": 39.9342,
                    "longitude": 116.4253,
                    "phone": "010-64018888",
                    "cuisine_type": "京菜",
                    "price_range": "¥¥¥¥",
                    "rating": 4.6,
                    "description": "高端烤鸭，艺术呈现",
                    "business_hours": "11:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1518492104633-130d0cc84637?w=400",
                    "platform_source": "美团",
                    "platform_id": "meituan_456789",
                },
                {
                    "name": "局气",
                    "address": "西城区地安门西大街51号",
                    "latitude": 39.9342,
                    "longitude": 116.3815,
                    "phone": "010-66176688",
                    "cuisine_type": "北京菜",
                    "price_range": "¥¥",
                    "rating": 4.4,
                    "description": "老北京风味，胡同文化体验",
                    "business_hours": "11:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",
                    "platform_source": "大众点评",
                    "platform_id": "dianping_567890",
                },
                {
                    "name": "西贝莜面村",
                    "address": "朝阳区望京街9号望京SOHO",
                    "latitude": 39.9890,
                    "longitude": 116.4810,
                    "phone": "010-57382888",
                    "cuisine_type": "西北菜",
                    "price_range": "¥¥",
                    "rating": 4.3,
                    "description": "西北风味，莜面必尝",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1547573854-74d2a71d0826?w=400",
                    "platform_source": "美团",
                    "platform_id": "meituan_678901",
                },
                {
                    "name": "云海肴",
                    "address": "朝阳区朝阳北路101号大悦城",
                    "latitude": 39.9219,
                    "longitude": 116.4634,
                    "phone": "010-85551188",
                    "cuisine_type": "云南菜",
                    "price_range": "¥¥",
                    "rating": 4.2,
                    "description": "云南特色，菌菇鲜美",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1541014741259-de529411b96a?w=400",
                    "platform_source": "美团",
                    "platform_id": "meituan_789012",
                },
                {
                    "name": "胜博殿",
                    "address": "朝阳区建国路87号SKP商场",
                    "latitude": 39.9087,
                    "longitude": 116.4609,
                    "phone": "010-65331188",
                    "cuisine_type": "日料",
                    "price_range": "¥¥¥",
                    "rating": 4.5,
                    "description": "日式炸猪排，外酥里嫩",
                    "business_hours": "11:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400",
                    "platform_source": "大众点评",
                    "platform_id": "dianping_890123",
                },
                {
                    "name": "外婆家",
                    "address": "海淀区丹棱街甲1号欧美汇购物中心",
                    "latitude": 39.9637,
                    "longitude": 116.3189,
                    "phone": "010-82872288",
                    "cuisine_type": "浙菜",
                    "price_range": "¥¥",
                    "rating": 4.4,
                    "description": "杭帮菜，茶香鸡必点",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=400",
                    "platform_source": "美团",
                    "platform_id": "meituan_901234",
                },
                {
                    "name": "太二酸菜鱼",
                    "address": "朝阳区东大桥路9号侨福芳草地",
                    "latitude": 39.9219,
                    "longitude": 116.4515,
                    "phone": "010-85618866",
                    "cuisine_type": "川菜",
                    "price_range": "¥¥",
                    "rating": 4.3,
                    "description": "网红酸菜鱼，酸爽开胃",
                    "business_hours": "11:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",
                    "platform_source": "大众点评",
                    "platform_id": "dianping_012345",
                },
            ]
            
            restaurants = [Restaurant(**data) for data in restaurants_data]
            session.add_all(restaurants)
            await session.flush()  # 获取餐厅ID
            print(f"✓ 插入 {len(restaurants)} 家餐厅")
            
            # 5. 插入示例笔记（5篇）
            notes_data = [
                {
                    "user_id": users[0].id,
                    "restaurant_id": restaurants[0].id,
                    "title": "🔥 老成都川菜馆探店 | 麻婆豆腐绝了！",
                    "content": "今天来到三里屯的老成都川菜馆，点了麻婆豆腐、水煮鱼、宫保鸡丁。麻婆豆腐真的太好吃了，麻辣鲜香，豆腐嫩滑。水煮鱼也很棒，鱼肉新鲜，辣椒香而不燥。强烈推荐！",
                    "images": ["https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400"],
                    "rating": 5.0,
                    "tags": ["川菜", "麻辣", "三里屯"],
                    "likes_count": 128,
                    "comments_count": 23,
                },
                {
                    "user_id": users[1].id,
                    "restaurant_id": restaurants[1].id,
                    "title": "🥟 鼎泰丰小笼包 | 米其林一星的实力",
                    "content": "鼎泰丰的小笼包果然名不虚传！皮薄馅大，汤汁鲜美。点了招牌小笼包、蟹粉小笼包、牛肉面。每一口都是享受，服务也很专业。推荐给大家！",
                    "images": ["https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=400"],
                    "rating": 4.8,
                    "tags": ["小笼包", "米其林", "国贸"],
                    "likes_count": 256,
                    "comments_count": 45,
                },
                {
                    "user_id": users[0].id,
                    "restaurant_id": restaurants[2].id,
                    "title": "🍲 海底捞火锅 | 服务堪比五星级酒店",
                    "content": "海底捞的服务真的是没话说！等位时有免费美甲、擦鞋，用餐时服务员超级贴心。点了番茄锅底、牛肉、虾滑，都很新鲜。虽然价格稍贵，但体验值回票价！",
                    "images": ["https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400"],
                    "rating": 4.9,
                    "tags": ["火锅", "服务好", "中关村"],
                    "likes_count": 189,
                    "comments_count": 34,
                },
                {
                    "user_id": users[1].id,
                    "restaurant_id": restaurants[3].id,
                    "title": "🦆 大董烤鸭 | 艺术品级别的烤鸭",
                    "content": "大董的烤鸭真是艺术品！鸭皮酥脆，鸭肉嫩滑，配菜精致。最喜欢蘸白糖吃鸭皮，入口即化。虽然价格不菲，但非常值得尝试！",
                    "images": ["https://images.unsplash.com/photo-1518492104633-130d0cc84637?w=400"],
                    "rating": 4.7,
                    "tags": ["烤鸭", "高端", "东四十条"],
                    "likes_count": 312,
                    "comments_count": 56,
                },
                {
                    "user_id": users[0].id,
                    "restaurant_id": restaurants[4].id,
                    "title": "🏠 局气 | 老北京味道",
                    "content": "局气的装修很有老北京特色，仿佛穿越回胡同时代。菜品味道地道，推荐局气豆腐、京酱肉丝。价格也很实惠，性价比很高！",
                    "images": ["https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400"],
                    "rating": 4.5,
                    "tags": ["京菜", "胡同风", "地安门"],
                    "likes_count": 145,
                    "comments_count": 28,
                },
            ]
            
            notes = [Note(**data) for data in notes_data]
            session.add_all(notes)
            print(f"✓ 插入 {len(notes)} 篇笔记")
            
            await session.commit()
            print("\n✅ 种子数据插入完成！")
            print(f"  - 菜系: {len(cuisines)} 个")
            print(f"  - 用户: {len(users)} 个")
            print(f"  - 餐厅: {len(restaurants)} 家")
            print(f"  - 笔记: {len(notes)} 篇")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 插入种子数据失败: {e}")
            raise


async def main():
    """主函数"""
    print("🚀 开始初始化数据库...\n")
    
    # 创建表
    await create_tables()
    
    # 插入种子数据
    await insert_seed_data()
    
    print("\n✅ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
