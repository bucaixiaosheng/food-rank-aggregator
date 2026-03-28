# 🍽️ 吃什么 - 餐饮聚合推荐平台

为吃货打造的多平台餐饮聚合推荐平台，汇聚大众点评、美团、小红书等多个平台的美食信息，通过AI智能推荐，帮您找到心仪的美食。

## 🌟 核心功能

- **多平台聚合**: 整合大众点评、美团、小红书等主流平台
- **智能推荐**: 基于用户口味画像的个性化推荐
- **探店笔记**: 分享美食体验，记录美好时刻
- **社交互动**: 点赞、评论、收藏，发现更多美食
- **排行榜**: 热门餐厅、新店推荐、口碑榜单

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代、快速的Python Web框架
- **SQLAlchemy** - ORM框架
- **SQLite** - 轻量级数据库
- **Playwright** - 爬虫框架
- **Pydantic** - 数据验证

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Vite** - 下一代前端构建工具
- **TailwindCSS** - 实用优先的CSS框架
- **Element Plus** - Vue 3 UI组件库
- **Pinia** - Vue 3 状态管理
- **Axios** - HTTP客户端

## 📦 项目结构

```
food-rank-aggregator/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── crawlers/       # 爬虫模块
│   │   ├── ai/             # AI推荐模块
│   │   ├── utils/          # 工具函数
│   │   └── core/           # 核心配置
│   ├── tests/              # 测试代码
│   └── run.py              # 启动脚本
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API封装
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   └── stores/        # 状态管理
│   └── package.json
├── data/                   # 数据存储
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- npm 或 yarn

### 后端安装

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### 前端安装

```bash
cd frontend
npm install
```

### 启动服务

**后端:**
```bash
cd backend
python run.py
```
访问: http://localhost:8000
API文档: http://localhost:8000/docs

**前端:**
```bash
cd frontend
npm run dev
```
访问: http://localhost:5173

## 📝 开发指南

### 数据库初始化
```bash
cd backend
python scripts/init_db.py
```

### 运行测试
```bash
cd backend
pytest
```

### 代码格式化
```bash
# Python
black app/
ruff check app/

# JavaScript
cd frontend
npm run lint
```

## 🔐 环境变量配置

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

主要配置项：
- `DATABASE_URL`: 数据库连接URL
- `CORS_ORIGINS`: 允许的跨域源
- `VITE_API_BASE_URL`: 前端API地址

## 📄 License

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**🍽️ 吃什么 - 让美食选择不再困难！**
