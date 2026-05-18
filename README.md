# ShutStart

Windows 开机启动管理器。开机后弹出一个对话框,左边一键关掉一批不想跑的自启软件 (A 类,例如远控类),右边按需启动一批没设自启的软件 (B 类,例如代理类),每个 B 项还可独立勾选"管理员模式"。

## 功能特点

- 开机自启,弹窗居中显示 (左右分列)
- A 类: 默认勾选,点确认后批量 `terminate` 选中进程
- B 类: 默认按配置勾选,可选管理员模式 (走 `ShellExecuteW runas`,触发 UAC)
- 单个"确认"按钮一次性执行,1.5 秒结果浮层后退出
- 点 X / 取消: 直接退出,什么都不做
- 内置 GUI 设置页面,无需手工编辑 JSON
- **外观主题** (v1.2): Claude 风 (奶油暖白 + 橙) / Mac 风 (浅灰 + Apple 蓝),设置页下拉切换、实时预览
- **窗口大小记忆** (v1.2): 拖大/拖小后下次打开自动还原
- 主题对应图标: 任务栏/窗口图标随主题切换
- 配置存 `%APPDATA%\ShutStart\config.json`,日志存 `%APPDATA%\ShutStart\shutstart.log`
- 自启通过 HKCU Run 注册表 (无需管理员)
- 安装包用 Inno Setup 打成 `ShutStart-Setup.exe`,安装到 `%LocalAppData%\Programs\ShutStart`,全程无 UAC

## 安装与使用 (普通用户)

1. 从仓库 [Releases](../../releases) 或最新一次成功的 [Actions](../../actions) workflow 下载 `ShutStart-Setup.exe`
2. 双击安装 (不需要管理员)
3. 安装结束后会自动弹出"设置"界面,添加要管理的 A/B 项,保存
4. 下次重启或登录时,会自动弹出主对话框

### 配置示例

**A 类 (要关的)**:
- 显示名: `AnyDesk`,进程名: `AnyDesk.exe`
- 显示名: `向日葵`,进程名: `SunloginClient.exe`, `SunloginRemoteDesk.exe`
- 显示名: `ToDesk`,进程名: `ToDesk.exe`

**B 类 (要启的)**:
- 显示名: `Clash Verge`,程序路径: `C:\Program Files\Clash Verge\Clash Verge.exe`,默认管理员: 是
- 显示名: `v2rayN`,程序路径: `D:\Tools\v2rayN\v2rayN.exe`,默认管理员: 否

## 已知限制

- 某些远控软件以 **Windows 服务** 形式运行 (例如 `ToDesk_Service.exe`),普通用户权限**无法** `terminate`。如果你需要关掉服务版本,可以右键 ShutStart 选"以管理员身份运行"一次,或者在服务管理器里直接禁用服务的自启。
- 程序运行时不再额外提权;每个勾选了"管理员"的 B 项会**独立**弹一次 UAC,这是 Windows 的限制,无法绕过。

## 本地开发 (源码运行)

```powershell
git clone <repo-url> D:\AI\shutstart
cd D:\AI\shutstart
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m shutstart
```

直接打开设置页:

```powershell
python -m shutstart --settings
```

> 本地**不**做最终打包。所有 PyInstaller + Inno Setup 流程都跑在 GitHub Actions 上。

## 远程构建 (GitHub Actions)

仓库已包含 `.github/workflows/build.yml`。两种触发方式:

**方式一: 手动触发 (推荐日常用)**
1. 把代码推到 GitHub (新仓库即可)
2. 进入 Actions → "Build Installer" → "Run workflow"
3. 等 3-5 分钟跑完,展开 job → Artifacts → 下载 `ShutStart-Setup`

**方式二: 推 tag 发版**
```powershell
git tag v1.0.0
git push --tags
```
会自动构建并在 Releases 页面挂出 `ShutStart-Setup.exe`。

## 图标生成

两档主题各自配套一个图标:

```
shutstart/resources/icon-claude.ico    # 暖橙 + 白色电源符号
shutstart/resources/icon-mac.ico       # Apple 蓝渐变 + 白色电源符号
shutstart/resources/icon.ico           # = icon-claude.ico 副本, 供 PyInstaller 内嵌
```

生成命令 (Pillow 已在 `requirements-build.txt`):

```powershell
pip install -r requirements-build.txt
python tools/make_icons.py
```

CI 已经在打包前自动跑这一步,不需要手动提交 ICO 文件。也可以自己改 `tools/make_icons.py` 调色板/形状。

> 自定义图标: 直接把符合命名的 ICO 文件替换进 `shutstart/resources/` 即可,会覆盖生成产物。

## 项目结构

```
shutstart/
├── __main__.py            # 入口
├── app.py                 # QApplication / HiDPI
├── config.py              # 读写 %APPDATA% 下的 config.json
├── autostart.py           # HKCU Run 注册表
├── killer.py              # psutil 终止 A 类进程
├── launcher.py            # subprocess + ShellExecuteW runas
├── ui/
│   ├── main_dialog.py     # 主对话框 (左右分列)
│   ├── settings_dialog.py # 设置 (A/B 列表 + 自启 + 主题)
│   ├── item_editor.py     # 单项编辑表单
│   └── themes.py          # QSS 主题 (Claude / Mac)
└── resources/             # 主题图标 (CI 生成)
tools/make_icons.py        # Pillow 程序化生成 ICO
installer/setup.iss        # Inno Setup 脚本
.github/workflows/build.yml # CI 构建流水线
build.spec                 # PyInstaller spec
version.txt                # Windows 文件元信息
```

## 卸载

通过"设置 → 应用 → ShutStart → 卸载"。卸载时会:
- 删除安装目录 (`%LocalAppData%\Programs\ShutStart`)
- 清除 HKCU\Run 中的 `ShutStart` 自启项
- **保留** `%APPDATA%\ShutStart\config.json` (用户配置),如需彻底清理可手动删除该目录
