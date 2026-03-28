"""
种子数据脚本 - 为餐饮聚合推荐平台填充初始数据
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.core.database import async_session_maker
from app.models.restaurant import Restaurant, Cuisine
from app.models.user import User, TasteProfile
from app.models.social import Note
from app.models.crawler import Ranking


async def seed_database():
    """填充种子数据"""
    # 先创建表
    from app.core.database import engine, Base
    from app.models import restaurant, user, social, crawler
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表已创建\n")
    
    async with async_session_maker() as db:
        try:
            # 1. 创建菜系分类
            cuisines_data = [
                {"name": "川菜", "description": "四川菜系，以麻辣著称", "icon": "🌶️"},
                {"name": "粤菜", "description": "广东菜系，清淡鲜美", "icon": "🥟"},
                {"name": "湘菜", "description": "湖南菜系，香辣浓郁", "icon": "🔥"},
                {"name": "日料", "description": "日本料理，新鲜精致", "icon": "🍣"},
                {"name": "西餐", "description": "西方料理，优雅浪漫", "icon": "🍝"},
                {"name": "火锅", "description": "涮煮美食，聚会首选", "icon": "🍲"},
                {"name": "烧烤", "description": "烤制美食，香气四溢", "icon": "🍢"},
                {"name": "快餐", "description": "快捷便利，经济实惠", "icon": "🍔"},
                {"name": "甜品", "description": "甜点饮品，治愈心情", "icon": "🍰"},
                {"name": "面食", "description": "面点小吃，传统美味", "icon": "🍜"},
            ]
            
            for cuisine_data in cuisines_data:
                cuisine = Cuisine(**cuisine_data)
                db.add(cuisine)
            
            await db.flush()
            print(f"✅ 已创建 {len(cuisines_data)} 个菜系分类")
            
            # 2. 创建餐厅数据
            restaurants_data = [
                {
                    "name": "蜀大侠火锅（朝阳店）",
                    "address": "北京市朝阳区建国路88号SOHO现代城B1层",
                    "latitude": 39.9087,
                    "longitude": 116.4605,
                    "phone": "010-85895678",
                    "cuisine_type": "川菜,火锅",
                    "price_range": "80-150元",
                    "rating": 4.8,
                    "description": "正宗川味火锅，毛肚黄喉必点。环境优雅，服务周到。",
                    "business_hours": "11:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800",
                    "platform_source": "dianping",
                },
                {
                    "name": "鮨一·日本料理",
                    "address": "北京市朝阳区三里屯太古里北区B1层",
                    "latitude": 39.9371,
                    "longitude": 116.4533,
                    "phone": "010-64176688",
                    "cuisine_type": "日料,刺身",
                    "price_range": "200-400元",
                    "rating": 4.7,
                    "description": "新鲜刺身，环境优雅，适合约会。主厨来自东京，手艺精湛。",
                    "business_hours": "11:30-14:00, 17:30-22:00",
                    "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=800",
                    "platform_source": "meituan",
                },
                {
                    "name": "老字号兰州拉面",
                    "address": "北京市东城区王府井大街138号",
                    "latitude": 39.9147,
                    "longitude": 116.4108,
                    "phone": "010-65281234",
                    "cuisine_type": "面食,西北",
                    "price_range": "15-35元",
                    "rating": 4.5,
                    "description": "二十年老店，牛肉面一绝。面条劲道，汤头浓郁。",
                    "business_hours": "07:00-21:00",
                    "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800",
                    "platform_source": "amap",
                },
                {
                    "name": "外婆家（西单店）",
                    "address": "北京市西城区西单北大街120号西单商场5层",
                    "latitude": 39.9139,
                    "longitude": 116.3742,
                    "phone": "010-66158888",
                    "cuisine_type": "浙菜,家常菜",
                    "price_range": "50-100元",
                    "rating": 4.6,
                    "description": "杭帮菜代表，性价比超高。茶香鸡、东坡肉必点。",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800",
                    "platform_source": "dianping",
                },
                {
                    "name": "木屋烧烤（五道口店）",
                    "address": "北京市海淀区成府路28号五道口购物中心B1层",
                    "latitude": 39.9917,
                    "longitude": 116.3383,
                    "phone": "010-62616688",
                    "cuisine_type": "烧烤,烤串",
                    "price_range": "60-120元",
                    "rating": 4.4,
                    "description": "深夜食堂首选，烤串种类丰富，氛围轻松。",
                    "business_hours": "17:00-02:00",
                    "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                    "platform_source": "meituan",
                },
                {
                    "name": "喜茶（国贸店）",
                    "address": "北京市朝阳区建国门外大街1号国贸商城B1层",
                    "latitude": 39.9087,
                    "longitude": 116.4595,
                    "phone": "010-65058888",
                    "cuisine_type": "甜品,饮品",
                    "price_range": "20-40元",
                    "rating": 4.7,
                    "description": "网红奶茶，芝芝莓莓、多肉葡萄必点。",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1558857563-b371033873b8?w=800",
                    "platform_source": "xiaohongshu",
                },
                {
                    "name": "绿茶餐厅（中关村店）",
                    "address": "北京市海淀区中关村大街19号新中关购物中心3层",
                    "latitude": 39.9847,
                    "longitude": 116.3158,
                    "phone": "010-82676688",
                    "cuisine_type": "浙菜,创意菜",
                    "price_range": "60-120元",
                    "rating": 4.5,
                    "description": "融合菜系，环境文艺，面包诱惑、龙井虾仁推荐。",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800",
                    "platform_source": "dianping",
                },
                {
                    "name": "肯德基（王府井店）",
                    "address": "北京市东城区王府井大街255号",
                    "latitude": 39.9147,
                    "longitude": 116.4108,
                    "phone": "010-65281235",
                    "cuisine_type": "快餐,炸鸡",
                    "price_range": "25-50元",
                    "rating": 4.2,
                    "description": "经典快餐，方便快捷。适合工作日午餐。",
                    "business_hours": "07:00-23:00",
                    "image_url": "https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=800",
                    "platform_source": "meituan",
                },
                {
                    "name": "西贝莜面村（望京店）",
                    "address": "北京市朝阳区望京街9号望京国际商业中心B1层",
                    "latitude": 39.9967,
                    "longitude": 116.4733,
                    "phone": "010-64738888",
                    "cuisine_type": "西北,面食",
                    "price_range": "60-120元",
                    "rating": 4.6,
                    "description": "西北风味，莜面、羊肉必点。适合家庭聚餐。",
                    "business_hours": "10:00-22:00",
                    "image_url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800",
                    "platform_source": "dianping",
                },
                {
                    "name": "海底捞火锅（三里屯店）",
                    "address": "北京市朝阳区三里屯路19号院1号楼",
                    "latitude": 39.9371,
                    "longitude": 116.4533,
                    "phone": "010-64176666",
                    "cuisine_type": "火锅,川菜",
                    "price_range": "100-180元",
                    "rating": 4.9,
                    "description": "服务业界标杆，免费美甲、甩面表演。番茄锅底经典。",
                    "business_hours": "10:00-次日02:00",
                    "image_url": "https://images.unsplash.com/photo-1555126634-323283e090fa?w=800",
                    "platform_source": "dianping",
                },
            ]
            
            for rest_data in restaurants_data:
                restaurant = Restaurant(**rest_data)
                db.add(restaurant)
            
            await db.flush()
            print(f"✅ 已创建 {len(restaurants_data)} 家餐厅")
            
            # 3. 创建测试用户
            user = User(
                nickname="美食家小王",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix",
                bio="资深吃货，热爱探索城市美食",
            )
            db.add(user)
            await db.flush()
            
            # 4. 创建用户口味画像
            taste_profile = TasteProfile(
                user_id=user.id,
                preferred_cuisines=["川菜", "日料", "火锅"],
                preferred_price_range="50-150元",
                preferred_spice_level=3,
                flavor_tags=["辣", "鲜", "香"],
                dietary_restrictions=[],
            )
            db.add(taste_profile)
            await db.flush()
            print(f"✅ 已创建测试用户和口味画像")
            
            # 5. 创建一些笔记
            notes_data = [
                {
                    "user_id": user.id,
                    "restaurant_id": 1,
                    "title": "蜀大侠火锅探店记",
                    "content": "今天和朋友来打卡了这家网红火锅店！毛肚超级新鲜，黄喉也很脆。锅底选的中辣，对于不太能吃辣的我来说刚刚好。服务态度很好，会推荐！",
                    "rating": 4.8,
                    "images": ["https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800"],
                    "tags": ["火锅", "川菜", "聚餐"],
                },
                {
                    "user_id": user.id,
                    "restaurant_id": 2,
                    "title": "三里屯的宝藏日料店",
                    "content": "鮨一的刺身真的太新鲜了！主厨是东京来的，手艺很棒。环境也很优雅，适合约会。推荐他们的特级寿司套餐。",
                    "rating": 4.7,
                    "images": ["https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=800"],
                    "tags": ["日料", "约会", "三里屯"],
                },
                {
                    "user_id": user.id,
                    "restaurant_id": 10,
                    "title": "海底捞的服务绝了！",
                    "content": "海底捞的服务真的是业界标杆，等位的时候还有免费零食和美甲。番茄锅底是永远的经典，甩面表演太精彩了！",
                    "rating": 4.9,
                    "images": ["https://images.unsplash.com/photo-1555126634-323283e090fa?w=800"],
                    "tags": ["火锅", "服务好", "网红店"],
                },
            ]
            
            for note_data in notes_data:
                note = Note(**note_data)
                db.add(note)
            
            await db.flush()
            print(f"✅ 已创建 {len(notes_data)} 篇笔记")
            
            # 6. 创建排行榜
            rankings_data = [
                {
                    "name": "全城美食榜",
                    "description": "北京最受欢迎的餐厅排行",
                    "ranking_type": "hot",
                    "restaurants": [10, 1, 2, 4, 6],
                    "is_active": True,
                },
                {
                    "name": "性价比之王",
                    "description": "好吃不贵的宝藏店铺",
                    "ranking_type": "value",
                    "restaurants": [3, 8, 4, 9],
                    "is_active": True,
                },
                {
                    "name": "新店推荐",
                    "description": "近期开业的优质餐厅",
                    "ranking_type": "new",
                    "restaurants": [2, 6, 7],
                    "is_active": True,
                },
            ]
            
            for ranking_data in rankings_data:
                ranking = Ranking(**ranking_data)
                db.add(ranking)
            
            await db.flush()
            print(f"✅ 已创建 {len(rankings_data)} 个排行榜")
            
            # 提交所有更改
            await db.commit()
            print("\n🎉 种子数据填充完成！")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 错误: {e}")
            raise


if __name__ == "__main__":
    print("🚀 开始填充种子数据...\n")
    asyncio.run(seed_database())
