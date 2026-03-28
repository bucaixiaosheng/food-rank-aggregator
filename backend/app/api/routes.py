"""
API路由配置 - 餐饮聚合推荐平台
包含搜索、餐厅、推荐、用户、收藏、打卡、笔记、社交、爬虫管理等全部API
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.restaurant import Restaurant, Cuisine
from app.models.user import User, TasteProfile, UserActivity
from app.models.social import Note, Comment, Follow, Favorite
from app.models.crawler import (
    CrawlTask, PlatformRating, Ranking, Blacklist,
)

api_router = APIRouter()


# ============================================================
# 统一响应模型
# ============================================================

class ApiResponse(BaseModel):
    """统一API响应"""
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    code: int = 200
    message: str = "success"
    data: dict | list  # 修改为支持 dict 或 list
    total: int
    page: int
    page_size: int


# ============================================================
# 请求/响应 Schema
# ============================================================

# --- 搜索 ---
class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词", min_length=1, max_length=200)
    location: Optional[str] = Field(None, description="位置，如：北京朝阳")
    filters: Optional[dict] = Field(None, description="筛选条件")


# --- 餐厅筛选 ---
class RestaurantFilterParams(BaseModel):
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    distance_max: Optional[float] = Field(None, description="最大距离(km)")
    rating_min: Optional[float] = None
    cuisine: Optional[str] = None
    business_status: Optional[str] = None


# --- 排行榜 ---
class RankingListItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    ranking_type: str
    restaurant_count: int = 0
    created_at: str


class RankingDetail(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    ranking_type: str
    restaurants: list = []
    is_active: bool = True


# --- 用户口味画像 ---
class TasteProfileUpdate(BaseModel):
    preferred_cuisines: Optional[list[str]] = None
    preferred_price_range: Optional[str] = None
    preferred_spice_level: Optional[int] = Field(None, ge=1, le=5)
    flavor_tags: Optional[list[str]] = None
    dietary_restrictions: Optional[list[str]] = None


class TasteProfileResponse(BaseModel):
    user_id: int
    nickname: str
    preferred_cuisines: Optional[list] = None
    preferred_price_range: Optional[str] = None
    preferred_spice_level: Optional[int] = None
    flavor_tags: Optional[list] = None
    dietary_restrictions: Optional[list] = None


# --- 收藏 ---
class FavoriteCreate(BaseModel):
    target_type: str = Field(..., description="收藏目标类型：restaurant/note")
    target_id: int
    group_name: Optional[str] = None


# --- 打卡 ---
class CheckinCreate(BaseModel):
    restaurant_id: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    comment: Optional[str] = None


# --- 笔记 ---
class NoteCreate(BaseModel):
    restaurant_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = None
    images: Optional[list[str]] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    tags: Optional[list[str]] = None


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = None


# --- 心情推荐 ---
class MoodRequest(BaseModel):
    mood: str = Field(..., description="心情：happy/sad/tired/romantic/angry/bored")
    extra: Optional[str] = None


# --- 爬虫 ---
class CrawlStartRequest(BaseModel):
    platform: str = Field(..., description="平台：dianping/meituan/amap/xiaohongshu")
    city: Optional[str] = None
    keywords: Optional[list[str]] = None


# --- 黑名单 ---
class BlacklistCreate(BaseModel):
    target_type: str = Field(..., description="类型：restaurant/user")
    target_id: int
    reason: Optional[str] = None


# ============================================================
# 1. 搜索和推荐API
# ============================================================

@api_router.post("/search", tags=["搜索和推荐"])
async def smart_search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    智能口味搜索 - 根据关键词、位置和筛选条件返回Top10推荐餐厅
    """
    query = select(Restaurant)
    # 简单的名称/菜系模糊匹配
    conditions = []
    conditions.append(Restaurant.name.contains(req.query))
    if req.location:
        conditions.append(Restaurant.address.contains(req.location) if req.location else True)
    query = query.where(or_(*conditions))
    query = query.order_by(desc(Restaurant.rating)).limit(10)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = [
        {
            "id": r.id, "name": r.name, "address": r.address,
            "cuisine_type": r.cuisine_type, "rating": r.rating,
            "price_range": r.price_range, "image_url": r.image_url,
        }
        for r in restaurants
    ]
    return ApiResponse(data=data)


@api_router.get("/restaurants", tags=["搜索和推荐"])
async def list_restaurants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cuisine: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    餐厅列表（分页）- 支持按菜系筛选
    """
    query = select(Restaurant)
    count_q = select(func.count()).select_from(Restaurant)
    if cuisine:
        query = query.where(Restaurant.cuisine_type.contains(cuisine))
        count_q = count_q.where(Restaurant.cuisine_type.contains(cuisine))

    total = (await db.execute(count_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = [
        {
            "id": r.id, "name": r.name, "address": r.address,
            "cuisine_type": r.cuisine_type, "rating": r.rating,
            "price_range": r.price_range, "image_url": r.image_url,
            "business_hours": r.business_hours,
        }
        for r in restaurants
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


@api_router.get("/restaurants/filter", tags=["筛选和排序"])
async def filter_restaurants(
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    distance_max: Optional[float] = None,
    rating_min: Optional[float] = None,
    cuisine: Optional[str] = None,
    business_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    多维筛选餐厅 - 支持价格、距离、评分、菜系、营业状态筛选
    """
    query = select(Restaurant)
    count_q = select(func.count()).select_from(Restaurant)

    if rating_min is not None:
        query = query.where(Restaurant.rating >= rating_min)
        count_q = count_q.where(Restaurant.rating >= rating_min)
    if cuisine:
        query = query.where(Restaurant.cuisine_type.contains(cuisine))
        count_q = count_q.where(Restaurant.cuisine_type.contains(cuisine))

    total = (await db.execute(count_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = [
        {
            "id": r.id, "name": r.name, "address": r.address,
            "cuisine_type": r.cuisine_type, "rating": r.rating,
            "price_range": r.price_range,
        }
        for r in restaurants
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


@api_router.get("/restaurants/{restaurant_id}", tags=["搜索和推荐"])
async def get_restaurant_detail(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    """
    餐厅详情 - 基本信息+多平台评分+评论摘要+优惠券
    """
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="餐厅不存在")

    # 获取多平台评分
    pr = await db.execute(
        select(PlatformRating).where(PlatformRating.restaurant_id == restaurant_id)
    )
    platform_ratings = [
        {
            "platform": p.platform, "rating": p.rating,
            "review_count": p.review_count, "tags": p.tags,
        }
        for p in pr.scalars().all()
    ]

    # 获取相关笔记
    nr = await db.execute(
        select(Note).where(Note.restaurant_id == restaurant_id).limit(3)
    )
    notes = [
        {"id": n.id, "title": n.title, "rating": n.rating, "user_id": n.user_id}
        for n in nr.scalars().all()
    ]

    data = {
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "latitude": restaurant.latitude,
        "longitude": restaurant.longitude,
        "phone": restaurant.phone,
        "cuisine_type": restaurant.cuisine_type,
        "price_range": restaurant.price_range,
        "rating": restaurant.rating,
        "description": restaurant.description,
        "business_hours": restaurant.business_hours,
        "image_url": restaurant.image_url,
        "platform_source": restaurant.platform_source,
        "platform_ratings": platform_ratings,
        "recent_notes": notes,
        "coupons": [],  # 优惠券预留
    }
    return ApiResponse(data=data)


# ============================================================
# 2. 排行榜API
# ============================================================

@api_router.get("/rankings", tags=["排行榜"])
async def list_rankings(
    ranking_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    排行榜列表 - 支持按类型筛选(hot/new/rating)
    """
    query = select(Ranking).where(Ranking.is_active == True)
    if ranking_type:
        query = query.where(Ranking.ranking_type == ranking_type)
    query = query.order_by(desc(Ranking.created_at))
    result = await db.execute(query)
    rankings = result.scalars().all()

    data = [
        {
            "id": r.id, "name": r.name, "description": r.description,
            "ranking_type": r.ranking_type,
            "restaurant_count": len(r.restaurants) if r.restaurants else 0,
            "created_at": str(r.created_at),
        }
        for r in rankings
    ]
    return ApiResponse(data=data)


@api_router.get("/rankings/{ranking_id}", tags=["排行榜"])
async def get_ranking_detail(ranking_id: int, db: AsyncSession = Depends(get_db)):
    """
    排行榜详情 - 包含餐厅列表
    """
    result = await db.execute(select(Ranking).where(Ranking.id == ranking_id))
    ranking = result.scalar_one_or_none()
    if not ranking:
        raise HTTPException(status_code=404, detail="排行榜不存在")

    data = {
        "id": ranking.id,
        "name": ranking.name,
        "description": ranking.description,
        "ranking_type": ranking.ranking_type,
        "restaurants": ranking.restaurants or [],
        "is_active": ranking.is_active,
    }
    return ApiResponse(data=data)


# ============================================================
# 3. 用户和口味画像API
# ============================================================

@api_router.get("/users/profile", tags=["用户和口味画像"])
async def get_user_profile(
    user_id: int = Query(1, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户口味画像
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    pr = await db.execute(
        select(TasteProfile).where(TasteProfile.user_id == user_id)
    )
    profile = pr.scalar_one_or_none()

    data = {
        "user_id": user.id,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "bio": user.bio,
        "taste_profile": {
            "preferred_cuisines": profile.preferred_cuisines if profile else None,
            "preferred_price_range": profile.preferred_price_range if profile else None,
            "preferred_spice_level": profile.preferred_spice_level if profile else None,
            "flavor_tags": profile.flavor_tags if profile else None,
            "dietary_restrictions": profile.dietary_restrictions if profile else None,
        } if profile else None,
    }
    return ApiResponse(data=data)


@api_router.put("/users/profile", tags=["用户和口味画像"])
async def update_user_profile(
    profile_in: TasteProfileUpdate,
    user_id: int = Query(1, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户口味偏好
    """
    result = await db.execute(select(TasteProfile).where(TasteProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = TasteProfile(user_id=user_id)
        db.add(profile)

    update_data = profile_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(profile, k, v)
    profile.updated_at = datetime.utcnow()
    await db.flush()

    return ApiResponse(data={"user_id": user_id, "message": "口味画像已更新"})


@api_router.get("/users/taste-tags", tags=["用户和口味画像"])
async def get_taste_tags(db: AsyncSession = Depends(get_db)):
    """
    获取可用的口味标签列表
    """
    tags = {
        "flavor_tags": ["甜", "咸", "酸", "辣", "麻", "鲜", "香", "清淡", "浓郁", "原味"],
        "cuisine_tags": ["川菜", "粤菜", "湘菜", "鲁菜", "日料", "韩餐", "西餐", "东南亚", "快餐", "烧烤", "火锅"],
        "spice_levels": [
            {"level": 1, "label": "不辣"},
            {"level": 2, "label": "微辣"},
            {"level": 3, "label": "中辣"},
            {"level": 4, "label": "重辣"},
            {"level": 5, "label": "变态辣"},
        ],
        "dietary_tags": ["素食", "无麸质", "低脂", "低糖", "高蛋白", "无海鲜", "无花生"],
    }
    return ApiResponse(data=tags)


@api_router.get("/recommendations/daily", tags=["用户和口味画像"])
async def get_daily_recommendations(
    user_id: int = Query(1, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    今日推荐 - 根据用户口味画像推荐3家餐厅
    """
    # 获取用户口味偏好
    pr = await db.execute(select(TasteProfile).where(TasteProfile.user_id == user_id))
    profile = pr.scalar_one_or_none()

    query = select(Restaurant).order_by(desc(Restaurant.rating)).limit(3)
    if profile and profile.preferred_cuisines:
        cuisine = profile.preferred_cuisines[0]
        query = select(Restaurant).where(
            Restaurant.cuisine_type.contains(cuisine)
        ).order_by(desc(Restaurant.rating)).limit(3)

    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = [
        {
            "id": r.id, "name": r.name, "cuisine_type": r.cuisine_type,
            "rating": r.rating, "price_range": r.price_range,
            "address": r.address, "reason": "根据您的口味偏好推荐",
        }
        for r in restaurants
    ]
    return ApiResponse(data={"date": str(datetime.utcnow().date()), "recommendations": data})


# ============================================================
# 4. 收藏夹和打卡API
# ============================================================

@api_router.post("/favorites", tags=["收藏和打卡"])
async def add_favorite(fav: FavoriteCreate, db: AsyncSession = Depends(get_db)):
    """
    添加收藏 - 收藏餐厅或笔记
    """
    user_id = 1  # TODO: 从认证中获取
    favorite = Favorite(
        user_id=user_id,
        target_type=fav.target_type,
        target_id=fav.target_id,
        group_name=fav.group_name,
    )
    db.add(favorite)
    await db.flush()
    return ApiResponse(data={"id": favorite.id, "message": "收藏成功"})


@api_router.get("/favorites", tags=["收藏和打卡"])
async def list_favorites(
    target_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    收藏列表 - 支持按类型筛选
    """
    user_id = 1
    query = select(Favorite).where(Favorite.user_id == user_id)
    count_q = select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    if target_type:
        query = query.where(Favorite.target_type == target_type)
        count_q = count_q.where(Favorite.target_type == target_type)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(desc(Favorite.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    favorites = result.scalars().all()

    data = [
        {"id": f.id, "target_type": f.target_type, "target_id": f.target_id,
         "group_name": f.group_name, "created_at": str(f.created_at)}
        for f in favorites
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


@api_router.delete("/favorites/{favorite_id}", tags=["收藏和打卡"])
async def delete_favorite(favorite_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除收藏
    """
    result = await db.execute(select(Favorite).where(Favorite.id == favorite_id))
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏不存在")
    await db.delete(favorite)
    await db.flush()
    return ApiResponse(data={"message": "已取消收藏"})


@api_router.post("/checkins", tags=["收藏和打卡"])
async def create_checkin(checkin: CheckinCreate, db: AsyncSession = Depends(get_db)):
    """
    打卡记录 - 在餐厅打卡
    """
    user_id = 1
    activity = UserActivity(
        user_id=user_id,
        activity_type="checkin",
        target_type="restaurant",
        target_id=checkin.restaurant_id,
        content=checkin.comment,
    )
    db.add(activity)
    await db.flush()
    return ApiResponse(data={"id": activity.id, "message": "打卡成功"})


@api_router.get("/checkins/map", tags=["收藏和打卡"])
async def get_checkin_map(
    user_id: int = Query(1, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    地图打卡数据 - 获取用户所有打卡的地理位置
    """
    result = await db.execute(
        select(UserActivity)
        .where(UserActivity.user_id == user_id, UserActivity.activity_type == "checkin")
        .order_by(desc(UserActivity.created_at))
    )
    activities = result.scalars().all()

    # 查找对应的餐厅信息
    data = []
    for a in activities:
        if a.target_id:
            rr = await db.execute(select(Restaurant).where(Restaurant.id == a.target_id))
            r = rr.scalar_one_or_none()
            if r:
                data.append({
                    "id": a.id, "restaurant_id": r.id, "restaurant_name": r.name,
                    "latitude": r.latitude, "longitude": r.longitude,
                    "address": r.address, "comment": a.content,
                    "created_at": str(a.created_at),
                })

    return ApiResponse(data=data)


# ============================================================
# 5. 探店笔记和社交API
# ============================================================

@api_router.post("/notes", tags=["探店笔记和社交"])
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db)):
    """
    发布探店笔记
    """
    user_id = 1
    n = Note(
        user_id=user_id,
        restaurant_id=note.restaurant_id,
        title=note.title,
        content=note.content,
        images=note.images,
        rating=note.rating,
        tags=note.tags,
    )
    db.add(n)
    await db.flush()
    return ApiResponse(data={"id": n.id, "message": "笔记发布成功"})


@api_router.get("/notes", tags=["探店笔记和社交"])
async def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    restaurant_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    笔记列表 - 支持按餐厅/用户筛选
    """
    query = select(Note)
    count_q = select(func.count()).select_from(Note)
    if restaurant_id:
        query = query.where(Note.restaurant_id == restaurant_id)
        count_q = count_q.where(Note.restaurant_id == restaurant_id)
    if user_id:
        query = query.where(Note.user_id == user_id)
        count_q = count_q.where(Note.user_id == user_id)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(desc(Note.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notes = result.scalars().all()

    data = [
        {
            "id": n.id, "title": n.title, "content": n.content[:100] if n.content else None,
            "images": n.images, "rating": n.rating, "tags": n.tags,
            "likes_count": n.likes_count, "comments_count": n.comments_count,
            "user_id": n.user_id, "restaurant_id": n.restaurant_id,
            "created_at": str(n.created_at),
        }
        for n in notes
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


@api_router.get("/notes/{note_id}", tags=["探店笔记和社交"])
async def get_note_detail(note_id: int, db: AsyncSession = Depends(get_db)):
    """
    笔记详情
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    # 获取评论
    cr = await db.execute(
        select(Comment).where(Comment.note_id == note_id).order_by(Comment.created_at).limit(20)
    )
    comments = [
        {"id": c.id, "user_id": c.user_id, "content": c.content,
         "likes_count": c.likes_count, "created_at": str(c.created_at)}
        for c in cr.scalars().all()
    ]

    data = {
        "id": note.id, "title": note.title, "content": note.content,
        "images": note.images, "rating": note.rating, "tags": note.tags,
        "likes_count": note.likes_count, "comments_count": note.comments_count,
        "user_id": note.user_id, "restaurant_id": note.restaurant_id,
        "created_at": str(note.created_at), "comments": comments,
    }
    return ApiResponse(data=data)


@api_router.post("/notes/{note_id}/like", tags=["探店笔记和社交"])
async def like_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """
    点赞笔记
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    note.likes_count += 1
    await db.flush()
    return ApiResponse(data={"note_id": note_id, "likes_count": note.likes_count})


@api_router.post("/notes/{note_id}/comments", tags=["探店笔记和社交"])
async def comment_note(note_id: int, comment: CommentCreate, db: AsyncSession = Depends(get_db)):
    """
    评论笔记 - 支持回复评论
    """
    user_id = 1
    # 验证笔记存在
    nr = await db.execute(select(Note).where(Note.id == note_id))
    if not nr.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="笔记不存在")

    c = Comment(
        user_id=user_id,
        note_id=note_id,
        parent_id=comment.parent_id,
        content=comment.content,
    )
    db.add(c)

    # 更新评论数
    note = nr.scalar_one_or_none()
    if note:
        note.comments_count += 1

    await db.flush()
    return ApiResponse(data={"id": c.id, "message": "评论成功"})


@api_router.post("/follow/{following_id}", tags=["探店笔记和社交"])
async def follow_user(following_id: int, db: AsyncSession = Depends(get_db)):
    """
    关注用户
    """
    follower_id = 1
    if follower_id == following_id:
        raise HTTPException(status_code=400, detail="不能关注自己")

    # 检查是否已关注
    existing = await db.execute(
        select(Follow).where(Follow.follower_id == follower_id, Follow.following_id == following_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已关注该用户")

    follow = Follow(follower_id=follower_id, following_id=following_id)
    db.add(follow)
    await db.flush()
    return ApiResponse(data={"message": "关注成功"})


@api_router.delete("/follow/{following_id}", tags=["探店笔记和社交"])
async def unfollow_user(following_id: int, db: AsyncSession = Depends(get_db)):
    """
    取消关注
    """
    follower_id = 1
    result = await db.execute(
        select(Follow).where(Follow.follower_id == follower_id, Follow.following_id == following_id)
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="未关注该用户")
    await db.delete(follow)
    await db.flush()
    return ApiResponse(data={"message": "已取消关注"})


@api_router.get("/followers/feed", tags=["探店笔记和社交"])
async def get_followers_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    关注动态 - 获取关注用户发布的笔记
    """
    user_id = 1
    # 获取关注列表
    fr = await db.execute(select(Follow.following_id).where(Follow.follower_id == user_id))
    following_ids = [r[0] for r in fr.all()]

    if not following_ids:
        return PaginatedResponse(data=[], total=0, page=page, page_size=page_size)

    query = select(Note).where(Note.user_id.in_(following_ids))
    count_q = select(func.count()).select_from(Note).where(Note.user_id.in_(following_ids))
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(desc(Note.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notes = result.scalars().all()

    data = [
        {
            "id": n.id, "title": n.title, "content": n.content[:100] if n.content else None,
            "images": n.images, "rating": n.rating,
            "likes_count": n.likes_count, "comments_count": n.comments_count,
            "user_id": n.user_id, "created_at": str(n.created_at),
        }
        for n in notes
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


# ============================================================
# 6. 天气/心情/随机推荐API
# ============================================================

@api_router.get("/recommendations/weather", tags=["天气/心情/随机推荐"])
async def weather_recommendations(
    weather: str = Query("sunny", description="天气：sunny/rainy/cloudy/cold/hot/snowy"),
    db: AsyncSession = Depends(get_db),
):
    """
    天气推荐 - 根据天气推荐餐厅类型
    """
    weather_map = {
        "sunny": "适合户外用餐，推荐露台餐厅和咖啡厅",
        "rainy": "下雨天推荐火锅和热汤面",
        "cloudy": "阴天适合吃点热乎的",
        "cold": "寒冷天气推荐火锅、串串",
        "hot": "炎热天气推荐冷面、冰品、日料",
        "snowy": "下雪天推荐暖身火锅",
    }

    # 根据天气推荐对应菜系
    cuisine_map = {
        "sunny": "咖啡厅", "rainy": "火锅", "cloudy": "川菜",
        "cold": "火锅", "hot": "日料", "snowy": "火锅",
    }
    cuisine = cuisine_map.get(weather, "中餐")

    query = select(Restaurant).where(
        Restaurant.cuisine_type.contains(cuisine)
    ).order_by(desc(Restaurant.rating)).limit(5)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = {
        "weather": weather,
        "suggestion": weather_map.get(weather, "不知道天气类型，随便推荐"),
        "recommendations": [
            {"id": r.id, "name": r.name, "cuisine_type": r.cuisine_type,
             "rating": r.rating, "address": r.address}
            for r in restaurants
        ],
    }
    return ApiResponse(data=data)


@api_router.post("/recommendations/mood", tags=["天气/心情/随机推荐"])
async def mood_recommendations(req: MoodRequest, db: AsyncSession = Depends(get_db)):
    """
    心情推荐 - 根据心情推荐餐厅
    """
    mood_map = {
        "happy": "开心就吃好的！推荐精致餐厅和甜品",
        "sad": "心情不好？来点甜食治愈一下",
        "tired": "累了就吃点简单暖心的",
        "romantic": "浪漫约会，推荐西餐和氛围餐厅",
        "angry": "生气就吃辣的发泄一下！",
        "bored": "无聊就尝试点新鲜的",
    }
    cuisine_map = {
        "happy": "西餐", "sad": "甜品", "tired": "快餐",
        "romantic": "西餐", "angry": "川菜", "bored": "日料",
    }
    cuisine = cuisine_map.get(req.mood, "中餐")

    query = select(Restaurant).where(
        Restaurant.cuisine_type.contains(cuisine)
    ).order_by(desc(Restaurant.rating)).limit(5)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = {
        "mood": req.mood,
        "suggestion": mood_map.get(req.mood, "保持好心情"),
        "recommendations": [
            {"id": r.id, "name": r.name, "cuisine_type": r.cuisine_type,
             "rating": r.rating, "address": r.address}
            for r in restaurants
        ],
    }
    return ApiResponse(data=data)


@api_router.get("/recommendations/random", tags=["天气/心情/随机推荐"])
async def random_recommendations(db: AsyncSession = Depends(get_db)):
    """
    随机推荐 - 随机推荐3家餐厅
    """
    query = select(Restaurant).order_by(func.random()).limit(3)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    data = [
        {"id": r.id, "name": r.name, "cuisine_type": r.cuisine_type,
         "rating": r.rating, "address": r.address, "image_url": r.image_url}
        for r in restaurants
    ]
    return ApiResponse(data=data)


# ============================================================
# 7. 黑名单API
# ============================================================

@api_router.get("/blacklist", tags=["黑名单"])
async def list_blacklist(
    target_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    黑名单列表
    """
    query = select(Blacklist)
    count_q = select(func.count()).select_from(Blacklist)
    if target_type:
        query = query.where(Blacklist.target_type == target_type)
        count_q = count_q.where(Blacklist.target_type == target_type)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(desc(Blacklist.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [
        {"id": b.id, "target_type": b.target_type, "target_id": b.target_id,
         "reason": b.reason, "created_at": str(b.created_at)}
        for b in items
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


@api_router.post("/blacklist", tags=["黑名单"])
async def add_to_blacklist(item: BlacklistCreate, db: AsyncSession = Depends(get_db)):
    """
    添加到黑名单
    """
    bl = Blacklist(target_type=item.target_type, target_id=item.target_id, reason=item.reason)
    db.add(bl)
    await db.flush()
    return ApiResponse(data={"id": bl.id, "message": "已加入黑名单"})


@api_router.delete("/blacklist/{blacklist_id}", tags=["黑名单"])
async def remove_from_blacklist(blacklist_id: int, db: AsyncSession = Depends(get_db)):
    """
    从黑名单移除
    """
    result = await db.execute(select(Blacklist).where(Blacklist.id == blacklist_id))
    bl = result.scalar_one_or_none()
    if not bl:
        raise HTTPException(status_code=404, detail="黑名单记录不存在")
    await db.delete(bl)
    await db.flush()
    return ApiResponse(data={"message": "已从黑名单移除"})


# ============================================================
# 8. 爬虫管理API
# ============================================================

@api_router.post("/crawl/start", tags=["爬虫管理"])
async def start_crawl(req: CrawlStartRequest, db: AsyncSession = Depends(get_db)):
    """
    启动爬虫任务 - 创建新的数据抓取任务
    """
    task = CrawlTask(
        platform=req.platform,
        status="pending",
    )
    db.add(task)
    await db.flush()
    return ApiResponse(data={
        "task_id": task.id,
        "platform": req.platform,
        "status": "pending",
        "message": f"爬虫任务已创建，平台：{req.platform}",
    })


@api_router.get("/crawl/status/{task_id}", tags=["爬虫管理"])
async def get_crawl_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    爬虫任务状态 - 查询任务执行进度
    """
    result = await db.execute(select(CrawlTask).where(CrawlTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    data = {
        "task_id": task.id,
        "platform": task.platform,
        "status": task.status,
        "started_at": str(task.started_at) if task.started_at else None,
        "finished_at": str(task.finished_at) if task.finished_at else None,
        "result_count": task.result_count,
        "error_message": task.error_message,
    }
    return ApiResponse(data=data)


@api_router.get("/crawl/history", tags=["爬虫管理"])
async def crawl_history(
    platform: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    爬取历史 - 查看所有爬虫任务记录
    """
    query = select(CrawlTask)
    count_q = select(func.count()).select_from(CrawlTask)
    if platform:
        query = query.where(CrawlTask.platform == platform)
        count_q = count_q.where(CrawlTask.platform == platform)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(desc(CrawlTask.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    data = [
        {
            "id": t.id, "platform": t.platform, "status": t.status,
            "started_at": str(t.started_at) if t.started_at else None,
            "finished_at": str(t.finished_at) if t.finished_at else None,
            "result_count": t.result_count, "error_message": t.error_message,
            "created_at": str(t.created_at),
        }
        for t in tasks
    ]
    return PaginatedResponse(data=data, total=total, page=page, page_size=page_size)


# ============================================================
# 9. 菜系API
# ============================================================

@api_router.get("/cuisines", tags=["基础数据"])
async def list_cuisines(db: AsyncSession = Depends(get_db)):
    """
    菜系列表 - 获取所有菜系分类
    """
    result = await db.execute(select(Cuisine).order_by(Cuisine.name))
    cuisines = result.scalars().all()
    data = [
        {"id": c.id, "name": c.name, "parent_id": c.parent_id,
         "description": c.description, "icon": c.icon}
        for c in cuisines
    ]
    return ApiResponse(data=data)


# ============================================================
# 10. 统计API
# ============================================================

@api_router.get("/stats", tags=["基础数据"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    平台统计数据
    """
    restaurant_count = (await db.execute(select(func.count()).select_from(Restaurant))).scalar() or 0
    note_count = (await db.execute(select(func.count()).select_from(Note))).scalar() or 0
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    crawl_count = (await db.execute(select(func.count()).select_from(CrawlTask))).scalar() or 0

    data = {
        "restaurant_count": restaurant_count,
        "note_count": note_count,
        "user_count": user_count,
        "crawl_task_count": crawl_count,
    }
    return ApiResponse(data=data)
