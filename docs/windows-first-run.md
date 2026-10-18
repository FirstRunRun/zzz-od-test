# Windows 首次 GUI 测试与独立应用准备

本阶段只验证个人版程序能在自己的电脑显示、切换和关闭界面，不启动、登录或操作游戏。
主项目使用固定提交 `52f82ddb076dd51b5a904f475e531411a2ddc432`。
云端 33 项测试不代表 Windows GUI 或游戏流程已经验证。

## 三种运行方式

| 方式 | 是什么 | 是否需要本机安装 Python |
|---|---|---|
| 源码运行 | Git 下载个人源码，uv 管理 Python 和依赖，再打开 GUI | uv 会准备，不需另装；适合第一次排错 |
| 独立压缩包 | `WithRuntime` 内含启动器、`.runtime`、`src`；解压完整目录后启动 exe | 不需要；普通包可能仍需联网下载模型 |
| 安装工具 | `OneDragon-Installer.exe` 选择目录并准备代码、运行环境和资源 | 由安装工具准备，可能联网；它不等同于已经制作好的 MSI 安装包 |

只复制一个 exe 不等于得到完整应用。`RuntimeLauncher.zip` 可以仅含启动器和运行时，
缺少 `src` 会被入口拒绝。完整离线模型包与普通 `WithRuntime` 也不同。
先验证源码 GUI，之后再验证私用压缩包；本阶段不制作正式 Release。

## 第一步：准备电脑

1. 建议使用 Windows 10/11 的 64 位电脑；准备网络及至少约 10 GB 空闲空间供源码、依赖和后续构建使用。
2. 关闭绝区零及游戏启动器。本次不要输入账号密码，不按 F9 等自动化快捷键。
3. 打开 PowerShell，逐行执行：

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
```

这是安装 Git 和 uv；如系统询问安装授权，先核对软件名称。
安装完成后关闭并重新打开 PowerShell，再检查：

```powershell
git --version
uv --version
```

若 winget 不可用，请从 Git for Windows 和 Astral uv 的官方安装说明安装，安装好再继续。

## 第二步：下载固定个人版本

逐行复制执行；出现红色错误就停止，保留完整错误文字。

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\OneDragonTest" | Out-Null
Set-Location "$env:USERPROFILE\OneDragonTest"
git clone --branch fix/first-round --single-branch https://github.com/FirstRunRun/ZenlessZoneZero-OneDragon.git OneDragon
Set-Location OneDragon
git switch --detach 52f82ddb076dd51b5a904f475e531411a2ddc432
git rev-parse HEAD
```

最后应显示上面的完整 SHA。这里的“分离 HEAD”只是固定测试版本，不修改 GitHub 的 main。
若 `OneDragon` 已存在，不要删除或覆盖旧目录；换一个空目录重新测试。

## 第三步：准备运行环境

仍在 `OneDragon` 目录执行：

```powershell
uv python install 3.11.17
uv sync --frozen --group dev --python 3.11.17
$env:PYTHONPATH = Join-Path (Get-Location).Path 'src'
uv run --no-sync python -c "import PySide6, cv2, numpy, onnxruntime, win32ui, pygit2; print('dependency import OK')"
```

最后应显示 `dependency import OK`。此步骤只导入依赖，不操作游戏。
`--frozen` 保留项目锁文件；不要把其他 Python 版本硬塞进这个环境。

主要依赖包括：PySide6/Fluent Widgets（界面）、OpenCV/NumPy（图片）、
ONNX Runtime DirectML（识别模型）、pywin32/pynput/pyautogui（Windows 输入和窗口）、
pygit2（版本管理），以及音频处理库。以项目锁文件为准。
当前项目限制 `pywin32<312` 以规避部分版本的 DLL 问题，不要单独升级它。
若出现 `VCRUNTIME`/`MSVCP` DLL 缺失，只从 Microsoft 官方修复/安装 Visual C++
2015–2022 Redistributable x64，不从 DLL 下载站下载零散文件。
虚拟手柄依赖属于 `gamepad` 可选组，本次默认键鼠 GUI 验证不启用，不要求安装手柄驱动。

## 第四步：打开界面

```powershell
uv run --no-sync python src/zzz_od/gui/app.py
```

1. 首次欢迎窗口属于正常现象。
2. 初始化可能提示下载 OCR 模型和公共资源；这不是账号登录，不需要提供游戏密码。
3. 等待初始化后，查看主页、设置和体力计划页面能否显示，再正常关闭窗口。
4. 不点击“开始”“运行”“进入游戏”“同步代码”等按钮，不按自动化快捷键。
5. 不修改账号配置，不启动后端游戏服务，也不使用 `--onedragon` 参数。

GUI 主窗口出现仅证明窗口创建成功。还要检查初始化是否完成、是否有错误提示、
页面能否切换、关闭是否正常；如果初始化失败，不应记录成 GUI 验证全部通过。
这条源码命令直接打开 GUI，不经过集成启动器的启动前代码同步。

建议记录：Windows 版本、CPU/显卡、当前 SHA、依赖安装结果、窗口是否显示、
初始化是否成功、页面切换和退出结果。失败时保存 PowerShell 错误及 `.log` 中的日志，
分享前检查是否含有账号信息；无需提供游戏密码。

## 后续打包的准备结论

- `deploy/OneDragon-Installer.spec`、`OneDragon-Launcher.spec`、
  `OneDragon-RuntimeLauncher.spec` 已提供 PyInstaller 配置。
- RuntimeLauncher 在 Windows 构建后将第三方运行时放在 `.runtime`；入口和文档均要求 `src` 配套存在。
- 打包会生成/更新 `deploy/module_manifest.py`；应在保留好修改的 Windows 构建副本进行，不能不经核对就提交生成结果。
- 原有 `build_full.bat` 并不能直接认定适合个人版：它还引用当前仓库不存在的 `uv.toml`，
  且其 RuntimeLauncher 压缩项不包含 `src`。后续需单独验证完整包内容，不能只看脚本退出。
- `tools/ci/prepare_release_assets.py` 涉及模型下载、打包和分发资产准备；本次没有执行它，
  也没有运行任何现有发布工作流。
- 集成启动器默认允许代码自动更新，原 `repository.yml` 的代码源是上游项目。
  个人版打包前必须单独确认 Fork 来源、目标版本及自动更新策略，避免覆盖个人修改；
  不能只复制一个 exe 就认为已得到固定个人版本。
- 独立应用不需要 Codex 常驻。普通 WithRuntime 仍可能需要首次联网下载模型；
  “无需 Python”“完全离线”“单文件 exe”是三件不同的事情。

## 哪些能在云端完成

Linux 云端可以完成源码分析、这 33 项测试、CI 报告、依赖清单和打包方案检查。
本次 CI 不会构建 exe，也不启动 GUI。
后续可单独设计 GitHub 的 Windows runner 私用构建任务，但它仍不能替代实际电脑验证。

你的 Windows 电脑需要完成：真实 GUI 显示、初始化、显卡/DirectML 和系统 DLL 兼容性、
关闭行为，以及未来私用包解压后的首次启动和更新策略验证。
未来制作的包还应在没有开发环境的干净 Windows 环境验证，才能确认没有遗漏依赖。
本阶段不包含实际游戏操作验证。
