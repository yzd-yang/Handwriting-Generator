# 手写生成器 - 桌面打包说明

本目录包含将「手写生成器」Web 应用打包成 Windows 桌面程序（文件夹版，免安装）的脚本和配置。

## 产物形态

打包后生成一个文件夹（可压缩成 zip 分发）：

```
手写生成器/
├── 手写生成器.exe          ← 用户双击这个（启动器）
├── _internal/              ← PyInstaller 运行时（可对用户隐藏）
├── frontend/               ← 前端构建产物（FastAPI 挂载）
├── font_assets/            ← 字体文件
├── pandoc/                 ← Pandoc 可执行文件（离线可用）
└── runtime/                ← 运行时生成的数据
    ├── logs/
    └── temp/
```

## 前置要求

1. **Python 3.10+**（打包机器）
2. **Node.js 18+**（构建前端）
3. **Pandoc MSI**（已放在 `backend/pandoc-3.10-windows-x86_64.msi`）

## 打包步骤

### 一键打包

```bat
cd packaging
build.bat
```

### 分步说明

1. **构建前端**
   ```bat
   cd frontendVite
   npm ci
   npm run build
   ```

2. **准备 Pandoc**
   ```bat
   cd packaging
   python fetch_pandoc.py
   ```
   如果自动解压失败，请手动将 `pandoc.exe` 放到 `packaging/pandoc/` 目录。

3. **打包后端**
   ```bat
   pyinstaller packaging/backend.spec --noconfirm
   ```

4. **打包启动器**
   ```bat
   pyinstaller packaging/launcher.spec --noconfirm
   ```

5. **组装产物**
   将 `dist/launcher.exe` 复制到 `dist/手写生成器/手写生成器.exe`

### 压缩分发

```bat
packaging\zip_release.bat v1.0.0
```

生成 `packaging/dist/手写生成器-v1.0.0.zip`

## 验证清单

在干净 Windows 机器（没装 Python、没装 Node）上验证：

- [ ] 双击 `手写生成器.exe`，2-5 秒内浏览器自动打开 `http://localhost:5005`
- [ ] 页面正常显示首页
- [ ] 字体列表加载正常
- [ ] 生成图片功能正常
- [ ] 托盘图标显示，右键退出正常
- [ ] 删除 `font_assets` 目录后启动有友好报错

## 常见问题

### 1. 杀毒软件误报

UPX 压缩可能触发 Windows Defender 误报。解决方法：
- 关闭 UPX：在 `backend.spec` 和 `launcher.spec` 里设置 `upx=False`
- 或给 exe 做代码签名

### 2. Pandoc 缺失

如果 `packaging/pandoc/pandoc.exe` 不存在，docx 导入功能会失败。

### 3. 前端 dist 不存在

先运行 `npm run build` 构建前端。

## 技术细节

- **PyInstaller --onedir**：文件夹模式，启动快，出错可看日志
- **前后端同源**：FastAPI 同时 serve 前端静态文件和后端 API，避免跨域
- **端口自动选择**：5005 被占则顺延到 5020
- **离线可用**：Pandoc 内嵌，无需联网下载

## 体积估算

| 部分 | 大小 |
|------|------|
| PyInstaller 后端 | ~280MB |
| 前端 dist | ~5MB |
| 字体文件 | ~22MB |
| Pandoc | ~40MB |
| **总计（未压缩）** | **~350MB** |
| **zip 压缩后** | **~150MB** |
