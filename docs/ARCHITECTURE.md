# 系统架构设计文档

## 1. 系统概述

"吃什么"餐饮聚合推荐平台是一个多平台数据聚合 + AI智能推荐的美食推荐系统。

### 1.1 核心目标

- 聚合美团、大众点评、小红书、高德等多个平台数据
- 通过AI算法提供个性化推荐
- 提供社交化的美食分享体验
- 支持多维度筛选和智能搜索

### 1.2 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue3 + Vite + TailwindCSS + Element Plus |
| 后端 | FastAPI + Python 3.12 |
| 数据库 | SQLite + SQLAlchemy ORM |
| 爬虫 | Playwright + httpx + BeautifulSoup |
| AI引擎 | 本地规则引擎 + TF-IDF |
| 地图 | 高德地图JS API |
| 部署 | Docker + Docker Compose |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────┐
│                    用户界面层                         │
│  Vue3 + TailwindCSS + Element Plus                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                    API网关层                         │
│  FastAPI + CORS + 认证中间件                         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                    业务逻辑层                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │搜索服务   │  │推荐服务   │  │社交服务   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │用户服务   │  │收藏服务   │  │笔记服务   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                    AI引擎层                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │口味解析   │  │评分引擎   │  │推荐算法   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │画像引擎   │  │天气推荐   │  │评论摘要   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                    爬虫引擎层                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │美团爬虫   │  │点评爬虫   │  │小红书爬虫  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│  ┌──────────┐  ┌──────────┐                       │
│  │高德爬虫   │  │数据清洗   │                       │
│  └──────────┘  └──────────┘                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                    数据存储层                        │
│  SQLite + SQLAlchemy ORM                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │餐厅表     │  │用户表     │  │笔记表     │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
用户搜索请求
    ↓
API网关（FastAPI）
    ↓
口味解析器（TasteParser）
    ↓
搜索服务（SearchService）
    ↓
┌─────────┬──────────┬──────────┐
│ 数据库   │ AI引擎   │ 爬虫引擎  │
│查询餐厅  │计算评分  │获取数据   │
└─────────┴──────────┴──────────┘
    ↓
推荐算法（RecommendationService）
    ↓
返回Top10结果
```

---

## 3. 核心模块设计

### 3.1 爬虫模块（Crawler Module）

#### 设计目标
- 支持多平台并发爬取
- 反爬策略（UA轮换、请求间隔、代理池）
- 数据清洗和去重
- 增量爬取

#### 类图

```
BaseCrawler (抽象基类)
    ├── MeituanCrawler
    ├── DianpingCrawler
    ├── XiaohongshuCrawler
    └── AmapCrawler

CrawlerEngine (调度器)
    └── 管理多个爬虫实例

DataCleaner (数据清洗器)
    └── 去重、合并、标准化
```

#### 反爬策略

```python
class AntiCrawlManager:
    - UserAgent轮换池（50+ UA）
    - 随机延迟（2-8秒）
    - 请求头伪装
    - Cookie管理
    - 频率限制器
```

### 3.2 AI推荐引擎（AI Engine）

#### 口味解析器（TasteParser）

```python
输入: "想吃辣的火锅"
输出: {
    "cuisine": "Sichuan",
    "dish": "hotpot",
    "spice_level": 4,
    "flavor_tags": ["spicy"],
    "confidence": 0.85
}
```

**实现方式**:
- 关键词映射表（500+关键词）
- 同义词扩展
- 模糊匹配（编辑距离）
- 置信度计算

#### 评分算法（ScoringEngine）

```python
总分 = 口味匹配度(30%) 
     + 平台评分(30%) 
     + 距离分数(15%) 
     + 价格匹配度(10%) 
     + 热度(10%) 
     + 新鲜度(5%)
```

**各维度计算**:

1. **口味匹配度** (0-1)
   ```python
   if user_cuisine == restaurant_cuisine:
       score = 1.0
   elif user_cuisine in related_cuisines:
       score = 0.7
   else:
       score = 0.3
   ```

2. **平台评分** (0-1)
   ```python
   score = rating / 5.0
   ```

3. **距离分数** (0-1)
   ```python
   score = 1 - (distance_km / max_distance_km)
   ```

4. **价格匹配度** (0-1)
   ```python
   if user_price == restaurant_price:
       score = 1.0
   else:
       score = 0.5
   ```

5. **热度** (0-1)
   ```python
   score = log(review_count) / max_log_reviews
   ```

6. **新鲜度** (0-1)
   ```python
   days_ago = (now - updated_at).days
   score = max(0, 1 - days_ago / 365)
   ```

#### 口味画像引擎（TasteProfileEngine）

```python
画像维度:
- preferred_cuisines: 偏好菜系列表
- preferred_spice_level: 辣度偏好 (1-5)
- flavor_tags: 口味标签
- taste_radar: 雷达图数据

更新策略:
- 每次搜索后异步更新
- 加权平均历史行为
- 指数衰减（近期行为权重更高）
```

### 3.3 数据模型（Data Models）

#### ER图

```
User (用户)
    ├── 1:N → UserActivity (活动记录)
    ├── 1:1 → TasteProfile (口味画像)
    ├── 1:N → Favorite (收藏)
    ├── 1:N → Note (笔记)
    ├── 1:N → Follow (关注)
    └── 1:N → Blacklist (黑名单)

Restaurant (餐厅)
    ├── 1:N → PlatformRating (平台评分)
    ├── 1:N → Note (笔记)
    ├── 1:N → Favorite (收藏)
    └── 1:N → Checkin (打卡)

Note (笔记)
    ├── N:1 → User (用户)
    ├── N:1 → Restaurant (餐厅)
    └── 1:N → Comment (评论)
```

#### 核心表结构

**restaurant表**:
```sql
CREATE TABLE restaurant (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    latitude FLOAT,
    longitude FLOAT,
    phone VARCHAR(50),
    cuisine_type VARCHAR(50),
    price_range VARCHAR(10),
    rating FLOAT,
    description TEXT,
    business_hours VARCHAR(200),
    image_url VARCHAR(500),
    platform_source VARCHAR(50),
    platform_id VARCHAR(100),
    created_at DATETIME,
    updated_at DATETIME
);
```

**platform_rating表**:
```sql
CREATE TABLE platform_rating (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER,
    platform VARCHAR(50),
    rating FLOAT,
    review_count INTEGER,
    tags JSON,
    platform_url VARCHAR(500),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (restaurant_id) REFERENCES restaurant(id)
);
```

---

## 4. API设计

### 4.1 RESTful API规范

- **Base URL**: `/api/v1`
- **认证**: JWT Token（未来）
- **版本**: URL路径版本控制
- **响应格式**: JSON

### 4.2 统一响应格式

```json
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2026-03-28T10:00:00Z"
}
```

### 4.3 错误处理

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "参数验证失败",
        "details": {...}
    }
}
```

---

## 5. 性能优化

### 5.1 数据库优化

- **索引策略**:
  ```sql
  CREATE INDEX idx_cuisine ON restaurant(cuisine_type);
  CREATE INDEX idx_rating ON restaurant(rating);
  CREATE INDEX idx_location ON restaurant(latitude, longitude);
  CREATE INDEX idx_user_activity ON user_activity(user_id, created_at);
  ```

- **查询优化**:
  - 使用异步查询（AsyncSession）
  - 分页查询避免全表扫描
  - 预加载关联数据（joinedload）

### 5.2 缓存策略

- **API响应缓存**:
  ```python
  @lru_cache(maxsize=1000)
  def get_restaurant_detail(restaurant_id):
      ...
  ```

- **推荐结果缓存**:
  - TTL: 5分钟
  - Key: hash(user_id + query + filters)
  - 存储在内存或Redis（未来）

### 5.3 前端优化

- **路由懒加载**:
  ```javascript
  const RestaurantDetail = () => import('./views/RestaurantDetailView.vue')
  ```

- **图片懒加载**:
  ```html
  <img v-lazy="restaurant.image_url" />
  ```

- **列表虚拟滚动**:
  ```vue
  <VirtualList :size="50" :remain="10">
    <RestaurantCard v-for="r in restaurants" :key="r.id" />
  </VirtualList>
  ```

---

## 6. 安全设计

### 6.1 反爬策略

- UserAgent轮换
- 随机延迟（2-8秒）
- 请求频率限制
- IP代理池（可选）
- 失败降级

### 6.2 数据安全

- 敏感信息加密存储
- SQL注入防护（ORM）
- XSS防护（前端转义）
- CORS配置

### 6.3 API安全

- 速率限制（60次/分钟）
- 参数验证（Pydantic）
- 错误信息脱敏

---

## 7. 扩展性设计

### 7.1 插件化爬虫

```python
class CrawlerPlugin:
    name: str
    platform: Platform
    priority: int
    
    async def crawl(self, **kwargs):
        ...
    
    async def parse(self, raw_data):
        ...

# 动态加载爬虫
engine.register_plugin(MyCrawlerPlugin())
```

### 7.2 推荐算法扩展

```python
class RecommendationStrategy(ABC):
    @abstractmethod
    async def recommend(self, context):
        ...

class TasteBasedStrategy(RecommendationStrategy):
    ...

class LocationBasedStrategy(RecommendationStrategy):
    ...

# 策略模式切换
engine.set_strategy(TasteBasedStrategy())
```

---

## 8. 部署架构

### 8.1 开发环境

```
Frontend (localhost:5173)
    ↓
Backend (localhost:8000)
    ↓
SQLite (./data/food_rank.db)
```

### 8.2 生产环境

```
Nginx (反向代理 + 静态资源)
    ↓
┌─────────┬─────────┐
│Frontend │ Backend │
│ (Docker)│ (Docker)│
└─────────┴─────────┘
    ↓
SQLite Volume (持久化)
```

---

## 9. 监控和日志

### 9.1 日志级别

- **DEBUG**: 开发调试信息
- **INFO**: 正常业务日志
- **WARNING**: 警告信息（爬虫失败）
- **ERROR**: 错误信息（异常）

### 9.2 监控指标

- API响应时间
- 爬虫成功率
- 数据库查询性能
- 内存使用率

---

## 10. 未来规划

### v2.0
- [ ] 引入Redis缓存
- [ ] 迁移PostgreSQL
- [ ] 用户认证系统
- [ ] 管理后台

### v3.0
- [ ] 移动端App
- [ ] AI大模型集成
- [ ] 实时推荐
- [ ] 语音搜索

---

## 11. 参考资料

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Vue3官方文档](https://vuejs.org/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Playwright文档](https://playwright.dev/python/)
