# 云端单元测试

`.github/workflows/cloud-unit-tests.yml` 在本测试仓 `fix/first-round` 每次 push 后运行。
不触发主项目的发布、签名、分发或游戏自动化。

## 两个仓库如何配对

- 主项目：`FirstRunRun/ZenlessZoneZero-OneDragon`，固定提交
  `52f82ddb076dd51b5a904f475e531411a2ddc432`。
- 测试项目：`FirstRunRun/zzz-od-test`，使用触发本次 push 的完整提交 SHA。
- 主项目检出到 `project/`，测试项目检出到 `project/zzz-od-test/`。
- 每次运行输出 `versions.json`，记录两个实际 SHA、Python 及主要依赖版本；CI 校验实际 SHA 与指定版本一致。
- 主项目日后有新代码时，需要在本工作流更新 `MAIN_SHA`，推送测试仓后才能验证新版本。
  主项目单独 push 不会触发本测试仓工作流，也不会自动改变被测版本。

## 范围与结果

| 文件 | 用例数量 |
|---|---:|
| `test/one_dragon/envs/test_repo_config.py` | 12（原有 10 + 参数传递 2） |
| `test/zzz_od/operation/test_restore_charge.py` | 15 |
| `test/one_dragon/utils/test_cv2_utils.py` | 6 |
| 合计 | 33 |

使用 Python 3.11、Ubuntu 24.04 和带 SHA-256 校验的 `ci/requirements.txt`。
这只是主项目 Windows 依赖中的独立测试子集，不代替完整 `uv.lock` 安装。

每个文件单独调用 pytest，使用 `--confcutdir` 限定 fixture 搜索范围，不加载依赖真实
Windows 上下文的全局 `test/conftest.py`。原测试文件、断言和用例选择不变，没有 skip、xfail
或条件过滤。三组都会执行；任何失败、错误、跳过或数量不符，整个工作流都会失败。
未纳入的其他游戏、OCR 模型和 GUI 测试不属于本工作流范围，不能宣称全仓测试通过。

日志和 Summary 展示结果，Artifact 保存三个 JUnit XML、`versions.json`、`summary.md`，保留 14 天。
如要长期保存，可在对应 Actions 运行页下载 Artifact。

## 本地复用

在配对好的主项目根目录，使用已安装这些依赖的 Python 运行：

```shell
python -m pip install --require-hashes -r zzz-od-test/ci/requirements.txt
python zzz-od-test/ci/run_cloud_tests.py
```

报告生成于主仓已忽略的 `.debug/cloud-unit-tests/`，不会修改源码和配置。
GitHub Actions 中依赖安装和 Ruff 也是必需检查；仅本地测试通过不等于远程 CI 已通过。

Windows 首次 GUI 验证及打包准备见 [Windows 首次测试](../docs/windows-first-run.md)。
