# Handwriting Web Backend

手写生成服务后端，基于 FastAPI。

## 快速启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 5005
```

## 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/generate_handwriting` | POST | 提交手写生成任务 |
| `/api/generate_handwriting/task/{task_id}` | GET | 查询任务状态 |
| `/api/generate_handwriting/task/{task_id}/result` | GET | 获取生成结果 |
| `/api/generate_handwriting/ws/{task_id}` | WebSocket | 实时任务状态推送 |
| `/api/fonts_info` | GET | 获取可用字体列表 |
| `/api/textfileprocess` | POST | 文档文本提取（支持 docx/pdf/txt/rtf） |
| `/api/imagefileprocess` | POST | 图片边距识别 |

## 并发架构

```
请求 → MAX_ACTIVE_TASKS=8（队列上限）→ Semaphore(2)（实际并发）→ 生成任务
```

- **MAX_ACTIVE_TASKS**：pending + processing 总数上限，超出返回 503
- **Semaphore(2)**：同时执行的生成任务数，通过 asyncio.Semaphore 控制

## 任务流程

1. 客户端提交请求 → 返回 `{ status: "accepted", task_id: "..." }`
2. 后台任务运行 `generate_handwriting_impl`，通过信号量控制并发
3. 任务状态存储在 SQLite（`tasks.db`，WAL 模式）
4. 大结果文件存储在 `temp/task_results/<task_id>/`
5. 客户端通过 WebSocket 或轮询获取任务状态
6. 任务完成后通过 `/result` 接口获取结果，结果自动删除
7. 任务 TTL：30 分钟

## 文档处理

### Word 文档导入

`/api/textfileprocess` 接口支持导入 `.docx` 文件，使用 pypandoc 转换为 HTML 格式，保留段落结构和格式信息。

转换流程：
1. pypandoc 将 docx 转换为完整 HTML 文档
2. 正则提取 `<body>` 内的 HTML 片段
3. 剥离 `<html><head><title>` 等包装标签
4. 返回 HTML 片段给前端 TiptapEditor 显示

### PDF 文档导入

PDF 文档使用 PyPDF2 提取文本，自动转换为 `<p>` 标签包裹的 HTML 格式，保留段落结构。

## 压测方法

### 环境准备

```bash
pip install locust
```

### 方式一：完整流程测试（测端到端体验）

模拟真实用户：提交任务 → 轮询等待 → 获取结果。

```bash
cd backend/tests
locust -f locustfile.py --host=http://127.0.0.1:5005 --headless -u 8 -r 1 --run-time 60s
```

**参数说明**：
- `-u 8`：8 个并发用户
- `-r 1`：每秒启动 1 个用户（预热）
- `--run-time 60s`：压测持续 60 秒

**关键指标**：
- 失败率 < 1%（在 8 并发以内）
- 单任务平均完成时间：3~8s

### 方式二：纯提交测试（测接口吞吐量）

只测 `/api/generate_handwriting` 接口，不管任务是否完成。

```bash
locust -f locustfile.py --host=http://127.0.0.1:5005 --headless -u 50 -r 10 --run-time 30s -t HandwritingSubmitOnly
```

### 方式三：UI 模式

```bash
locust -f locustfile.py --host=http://127.0.0.1:5005
```

浏览器打开 http://localhost:8089 进行配置和压测。

### 方式四：使用 pytest 压测

```bash
cd backend
HANDWRITING_BASE_URL=http://127.0.0.1:5005 \
HANDWRITING_LOAD_REQUESTS=6 \
HANDWRITING_LOAD_CONCURRENCY=4 \
pytest tests/test_generate_concurrency.py -v
```

## 性能数据

### 实际压测结果（Locust，8 并发用户，60s）

| 接口 | 请求数 | 失败率 | 平均耗时 | P95 耗时 |
|------|--------|--------|---------|---------|
| GET /api/fonts_info | 8 | 0% | 4.8s | 7.4s |
| POST /api/generate_handwriting | 28 | 0% | 9.4s | 17s |
| GET /task/{id}/status | 6 | 0% | 3~17s | - |
| GET /task/{id}/result | 5 | 0% | ~100ms | - |

**汇总：47 请求，0 失败，失败率 0%**

### 性能瓶颈分析

| 并发数 | 失败率 | 说明 |
|--------|--------|------|
| 8 | **0%** | 安全范围 |
| 16 | > 50% | 触发 503 队列满 |
| 50 | > 90% | 大部分请求被拒绝 |

**瓶颈**：
- Semaphore(2) 限制实际并发执行数为 2
- CPU 密集渲染任务受 GIL 限制
- 每个任务平均耗时 ~17s（RPS 约 0.5）

## 注意事项

1. **503 队列满**：当活跃任务数达到 8 时，新请求会被拒绝
2. **429 CPU 过载**：当 CPU 使用率 > 90% 时，任务会被限流
3. **压测建议**：先小规模压测（8 并发），确认稳定后再逐步加压
4. **临时文件**：后端在 `./temp/` 和 `./textfileprocess/` 目录生成临时文件，清理为尽力而为
5. **字体同步**：启动时自动同步 `FONT_ASSETS_BUNDLED_DIR` 到 `FONT_ASSETS_DIR`
