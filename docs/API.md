# API文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: 暂无（演示版本）
- **响应格式**: JSON

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## API端点列表

### 1. 搜索和推荐

#### POST /search
智能口味搜索

**请求参数:**
```json
{
  "query": "想吃辣的火锅",
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "filters": {
    "price_range": "¥¥",
    "max_distance_km": 5
  }
}
```

**响应:**
```json
{
  "restaurants": [
    {
      "id": 1,
      "name": "川味火锅",
      "cuisine_type": "Sichuan",
      "rating": 4.5,
      "price_range": "¥¥",
      "address": "朝阳区...",
      "distance_km": 2.3,
      "ai_summary": "味道正宗，分量足",
      "score": 0.92
    }
  ],
  "total_count": 10,
  "query_parsed": {
    "cuisine": "Sichuan",
    "dish": "hotpot",
    "spice_level": 4
  }
}
```

#### GET /restaurants
获取餐厅列表（分页）

**查询参数:**
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `cuisine`: 菜系过滤
- `price_range`: 价格区间
- `rating_min`: 最低评分

#### GET /restaurants/{id}
获取餐厅详情

**响应包含:**
- 基本信息
- 多平台评分对比
- AI评论摘要
- 优惠券信息
- 附近推荐

### 2. 筛选和排序

#### GET /restaurants/filter
多维筛选

**查询参数:**
- `price_min`: 最低价格
- `price_max`: 最高价格
- `distance_max`: 最大距离（公里）
- `rating_min`: 最低评分
- `cuisine`: 菜系
- `business_status`: 营业状态

#### GET /rankings
排行榜列表

**响应:**
```json
{
  "rankings": [
    {
      "id": 1,
      "name": "全城美食Top50",
      "type": "comprehensive",
      "updated_at": "2026-03-28T10:00:00Z"
    }
  ]
}
```

#### GET /rankings/{id}
排行榜详情

### 3. 用户和口味画像

#### GET /users/profile
获取用户口味画像

**响应:**
```json
{
  "user_id": 1,
  "taste_profile": {
    "preferred_cuisines": ["Sichuan", "Japanese"],
    "preferred_spice_level": 4,
    "flavor_tags": ["spicy", "fresh"],
    "taste_radar": {
      "spicy": 0.8,
      "sweet": 0.3,
      "sour": 0.5,
      "salty": 0.6,
      "fresh": 0.7,
      "light": 0.2
    }
  },
  "taste_tags": ["辣王", "日料控"]
}
```

#### PUT /users/profile
更新口味偏好

#### GET /users/taste-tags
获取口味标签

#### GET /recommendations/daily
今日推荐（3家）

### 4. 收藏夹和打卡

#### POST /favorites
添加收藏

**请求参数:**
```json
{
  "restaurant_id": 1,
  "group_name": "想去"
}
```

#### GET /favorites
收藏列表

**查询参数:**
- `group`: 分组名称

#### DELETE /favorites/{id}
删除收藏

#### POST /checkins
打卡记录

**请求参数:**
```json
{
  "restaurant_id": 1,
  "note": "味道不错",
  "rating": 5,
  "images": ["url1", "url2"]
}
```

#### GET /checkins/map
地图打卡数据

**响应:**
```json
{
  "checkins": [
    {
      "id": 1,
      "restaurant_id": 1,
      "restaurant_name": "川味火锅",
      "latitude": 39.9042,
      "longitude": 116.4074,
      "checked_at": "2026-03-28T10:00:00Z"
    }
  ]
}
```

### 5. 探店笔记和社交

#### POST /notes
发布笔记

**请求参数:**
```json
{
  "restaurant_id": 1,
  "title": "今天吃的这家火锅超赞",
  "content": "...",
  "images": ["url1", "url2"],
  "rating": 5,
  "tags": ["火锅", "辣"]
}
```

#### GET /notes
笔记列表

**查询参数:**
- `sort`: 排序方式（hot/latest）
- `restaurant_id`: 餐厅ID过滤
- `page`: 页码

#### POST /notes/{id}/like
点赞

#### POST /notes/{id}/comments
评论

**请求参数:**
```json
{
  "content": "看着很好吃！"
}
```

#### POST /follow/{user_id}
关注用户

#### GET /followers/feed
关注动态

### 6. 天气/心情/随机推荐

#### GET /recommendations/weather
天气推荐

**响应:**
```json
{
  "weather": {
    "temperature": 28,
    "condition": "晴"
  },
  "recommendations": [
    {
      "restaurant": {...},
      "reason": "夏天适合吃凉皮"
    }
  ]
}
```

#### POST /recommendations/mood
心情推荐

**请求参数:**
```json
{
  "mood": "happy"  // happy/sad/tired/celebrate
}
```

#### GET /recommendations/random
随机推荐（摇一摇）

#### GET /blacklist
黑名单管理

#### POST /blacklist
添加到黑名单

**请求参数:**
```json
{
  "type": "restaurant",  // restaurant/cuisine
  "target_id": 1
}
```

#### DELETE /blacklist/{id}
移出黑名单

### 7. 爬虫管理

#### POST /crawl/start
启动爬虫

**请求参数:**
```json
{
  "platform": "meituan",  // meituan/dianping/xiaohongshu/amap
  "city": "北京",
  "keyword": "火锅"
}
```

**响应:**
```json
{
  "task_id": "abc123",
  "status": "running"
}
```

#### GET /crawl/status/{task_id}
爬虫状态

**响应:**
```json
{
  "task_id": "abc123",
  "status": "completed",
  "result_count": 50,
  "started_at": "2026-03-28T10:00:00Z",
  "finished_at": "2026-03-28T10:05:00Z"
}
```

#### GET /crawl/history
爬取历史

## 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 速率限制

- 搜索API: 60次/分钟
- 其他API: 120次/分钟

## 版本历史

- v1.0.0 (2026-03-28): 初始版本
