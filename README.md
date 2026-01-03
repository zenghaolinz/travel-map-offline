这里为您根据上传的代码文件生成的 **README.md** 文档。您可以直接复制以下内容保存为 `README.md` 文件。

---

# Travel Map AI (Local Edition)

**Travel Map AI** 是一个基于 3D 地球可视化的智能旅行路线生成工具。它利用本地 AI 模型（Ollama/Qwen3）解析自然语言行程，或通过 OCR 识别行程单图片，自动在 CesiumJS 地球上生成动态的旅行路线动画。

本项目专为本地运行设计，支持“导演模式”进行路线漫游和视频录制。

## ✨ 主要功能

* **🌍 3D 地球可视化**: 基于 [CesiumJS](https://cesium.com/platform/cesiumjs/)，提供电影级的三维地图展示。
* **🧠 AI 智能规划**: 集成本地 **Ollama (Qwen3:8b)** 模型，支持输入自然语言（如“先去北京再去上海然后飞东京”）自动提取路线。
* **🖼️ 图片识别 (OCR)**: 支持上传行程单截图，使用 **Tesseract-OCR** 自动识别文字并生成路线。
* **🎬 导演模式 (Director Mode)**:
* 自动生成漫游动画，平滑的相机运镜。
* 支持调节播放速度 (0.5x - 3.0x)。
* 自动匹配交通工具图标（飞机 ✈️、火车 🚄、汽车 🚗）。
* 支持高度动态调整（避免遮挡）和正弦波速度曲线（模拟真实加减速）。


* **📍 手动路线规划**: 提供手动添加站点、选择交通工具的编辑器。
* **🎥 视频录制**: 内置录屏功能，可将生成的路线动画保存为 `.webm` 视频文件。
* **🌐 离线/在线混合**: 内置常用城市坐标数据库 (`assets/locations.json`)，未知地点自动回退查询在线 Geocoding API。

## 🛠️ 技术栈

* **后端**: Python 3.12+, FastAPI, Uvicorn
* **AI & OCR**: Ollama (Qwen3:8b), Tesseract-OCR, Pytesseract
* **前端**: HTML5, JavaScript, CesiumJS (CDN), TailwindCSS (CDN), Lucide Icons
* **数据处理**: Pillow (图像处理), Httpx (异步请求)

## ⚙️ 环境准备与安装

在运行项目之前，请确保您的环境满足以下要求：

### 1. 安装 Python 依赖

确保已安装 Python 3.12+，然后在项目根目录下安装所需库：

```bash
pip install fastapi uvicorn[standard] httpx pillow pytesseract

```

### 2. 配置本地 AI (Ollama)

本项目依赖 Ollama 运行本地大模型来解析行程意图。

1. 下载并安装 [Ollama](https://ollama.com/)。
2. 在终端中拉取 `qwen3:8b` 模型（代码中指定使用此模型）：
```bash
ollama run qwen3:8b

```


3. 确保 Ollama 服务正在运行 (默认端口 11434)。

### 3. 安装 OCR 工具 (Tesseract)

本项目使用 Tesseract 进行图片文字识别。

1. 下载并安装 [Tesseract-OCR](https://www.google.com/search?q=https://github.com/UB-Mannheim/tesseract/wiki)。
2. **重要配置**: 打开 `services.py` 文件，找到第 10 行，修改为您本地的 Tesseract 安装路径：
```python
# services.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # 修改为您实际的安装路径

```



## 🚀 启动项目

### 方法一：使用启动脚本 (Windows)

项目包含一个 `启动.bat` 脚本，但您需要根据自己的路径进行修改：

1. 右键编辑 `启动.bat`。
2. 修改 Python 解释器路径 (`D:\travel map\.venv\Scripts\python.exe`) 为您本地环境的路径。
3. 双击运行 `启动.bat`。

### 方法二：手动启动 (推荐)

1. 在项目根目录打开终端/命令行。
2. 启动后端服务：
```bash
uvicorn main:app --reload

```


3. 服务启动后，在浏览器中打开 `index.html` 文件（或者访问 `http://localhost:8000/index.html`，如果静态文件已正确挂载）。
* *注意：直接双击 `index.html` 可能因跨域问题无法加载资源，建议通过 FastAPI 的静态文件服务访问，或者使用 Live Server。*



## 📂 文件结构说明

```
.
├── assets/                 # 静态资源目录
│   ├── flags/              # 国家/地区旗帜 SVG
│   ├── locations.json      # 本地城市坐标数据库
│   ├── car.png, train.png  # 交通工具图标
│   └── ...
├── main.py                 # FastAPI 后端入口，API 路由定义
├── services.py             # 核心业务逻辑 (OCR, AI调用, 坐标查询)
├── index.html              # 前端主页面 (CesiumJS 地图与交互逻辑)
├── 启动.bat                # Windows 快速启动脚本
└── ...

```

## 📝 使用指南

1. **AI 生成**: 在底部输入框输入行程（例如：“从北京飞往伦敦，然后去巴黎”），点击右侧 ✨ 按钮。
2. **图片识别**: 点击底部输入框左侧的图片图标，上传行程单截图。
3. **手动规划**: 点击右上角“手动规划”按钮，逐个添加站点并指定交通方式。
4. **导演模式**: 路线生成后，点击右上角“导演模式”。进入后点击 **ACTION!** 开始播放动画。
5. **录制**: 在动画播放倒计时开始时，系统会自动开始录制，动画结束自动下载视频文件。

## ⚠️ 常见问题

* **Ollama 报错**: 请检查 Ollama 是否已启动，且是否已下载 `qwen3:8b` 模型。
* **OCR 无法识别**: 请检查 Tesseract 路径在 `services.py` 中是否配置正确，且图片清晰度足够。
* **地图不显示**: 前端依赖 Cesium 的 CDN，请确保您的网络可以访问 `cesium.com` 和 `unpkg.com`。

---

*Created by NLin*
