# ShutStart

Windows 开机启动管理器。开机后弹出一个对话框,左边一键关掉一批不想跑的自启软件 (A 类,例如远控类),右边按需启动一批没设自启的软件 (B 类,例如代理类),每个 B 项还可独立勾选"管理员模式"。设置里另外提供"本机启动项管理"页,直接管理 Windows 注册表 / 启动文件夹下的自启动条目 (主软件程序,默认屏蔽服务类)。

## 功能特点

- 开机自启,弹窗居中显示 (左右分列)
- A 类: 默认勾选,点确认后**强力终止**选中项 —— 连同子进程 (整棵进程树) 一起结束,且"先挂起再结束、杀完重扫复查",专治远控 / RMM 类"守护进程把主程序立刻重新拉起"导致的关不干净;进程名匹配大小写不敏感、`.exe` 可省略
- **实时检测**: 主弹窗每 2 秒自动重扫一次 (也可点「⟳ 刷新」立即重扫)。开机时即便 ShutStart 比远控软件先启动,晚到的进程也会被自动检出并按默认勾上,无需关掉重开;已手动改过的勾选不会被刷新覆盖
- B 类: 默认按配置勾选,可选管理员模式 (走 `ShellExecuteW runas`,触发 UAC)
- 单个"确认"按钮一次性执行,1.5 秒结果浮层后退出
- 点 X / 取消: 直接退出,什么都不做
- 内置 GUI 设置页面,无需手工编辑 JSON
- **外观主题**: Claude 风 (奶油暖白 + 橙) / Mac 风 (浅灰 + Apple 蓝),设置页下拉切换、实时预览
- **窗口大小记忆**: 拖大/拖小后下次打开自动还原
- **关闭倒计时**: 主对话框打开后,30 秒~10 分钟可调,归零自动取消并退出 (避免开机弹窗忘记处理)
- **本机启动项管理**: 设置顶栏新增按钮,枚举 `HKCU` / `HKLM` 下 `Run` / `RunOnce` (含 `Wow6432Node`) 和用户/公共启动文件夹的所有自启动条目;启用/禁用走 Windows 任务管理器同款的 `StartupApproved` 软禁用 (`0x02`/`0x03`),原条目保留可恢复;默认屏蔽服务类自启动 (`System32` / `*Service.exe` / `*Update.exe` 等),可通过复选框显示;HKLM / 公共启动项只读 (需要管理员权限)
- 主题对应图标: 任务栏/窗口图标随主题切换
- **管理员模式自启 (免 UAC)**: 设置页可勾选"以管理员身份启动 (任务计划器)",改用 Windows 任务计划器 + 登录触发 + 最高权限运行;首次创建/取消时各弹一次 UAC,之后每次开机静默以管理员身份运行,可关闭 SYSTEM 服务进程 (AweSun / ToDesk_Service 等)
- 配置存 `%APPDATA%\ShutStart\config.json`,日志存 `%APPDATA%\ShutStart\shutstart.log`
- 自启默认走 HKCU\Run 注册表 (普通用户); 启用管理员模式后改走 `\ShutStart\ShutStart Logon` 任务计划项
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

### 本机启动项管理

设置对话框顶栏点 **「本机启动项管理…」** 打开。能看到本机所有"应用类"自启动条目:

- **来源**: `HKCU\Run` / `HKCU\RunOnce` / `HKLM\Run` / `HKLM\RunOnce` / `HKLM\Wow6432Node\Run` / `HKLM\Wow6432Node\RunOnce` / `Startup (用户)` / `Startup (公共)`
- **启用/禁用**: 右侧复选框,效果与 Windows **任务管理器 → 启动应用** 页完全一致 —— 写 `…\Explorer\StartupApproved\Run` 二进制值首字节 (`0x02` 启用 / `0x03` 禁用),**不删除原 Run 条目**,可随时勾回来。
- **过滤**: 默认隐藏服务类条目 (文件名匹配 `Service` / `Svc` / `Daemon` / `Agent` / `Update` / `Updater` / `Helper`,或路径位于 `System32` / `SysWOW64` 之下,或值名包含 `Service`/`Svc`)。勾选"显示服务类自启动项"后整行灰色显示,后缀 `(服务类)`,该选项持久化到 `config.json`。
- **HKLM / 公共启动项**: 只读显示,复选框灰掉并提示"需要管理员权限"。如需启用/禁用 HKLM 项,用 Windows 任务管理器并以管理员身份运行;或在服务管理器里禁用真正的"服务"。

## 已知限制

- **关不干净 / 关掉又自己起来**: 远控类常是"主程序 + 守护进程"结构。ShutStart 终止时已自动连子进程 (整棵进程树) 一起杀、先挂起再结束、并多轮重扫复查;但若某个守护进程**既不在你填的进程名列表里、又不是主程序的子进程** (而是独立的同级 / 服务进程),它仍可能把主程序重新拉起。根治办法:把该软件的**所有**相关进程名都填进 A 项的"进程名" (例如向日葵填 `SunloginClient.exe` + `SunloginRemoteDesk.exe`,新版再加 `AweSun.exe` + `awesun_guard.exe`)。编辑关闭项时点「从运行中的进程选择…」可一次勾全 (默认勾上"显示系统进程"才能看到服务类)。
- 某些远控软件以 **Windows 服务** 形式运行 (例如 `ToDesk_Service.exe`、向日葵新版的 `AweSun.exe` + `awesun_guard.exe`),普通用户权限**无法** `terminate`。推荐做法:在设置里勾上 **"以管理员身份启动 (任务计划器, 免 UAC)"** —— 首次勾选会弹一次 UAC 创建登录任务,之后每次开机 ShutStart 静默以管理员身份运行,可正常 terminate 这类 SYSTEM 服务进程。取消勾选时同样会弹一次 UAC 删除任务。卸载时,若任务残留可手动到 `任务计划程序 → ShutStart → ShutStart Logon` 删除。
- 程序运行时不再额外提权;每个勾选了"管理员"的 B 项会**独立**弹一次 UAC,这是 Windows 的限制,无法绕过。
- **本机启动项管理**只接管 `Run` / `RunOnce` 注册表和启动文件夹的"应用类"自启动,不触碰 `HKLM\SYSTEM\CurrentControlSet\Services` 系统服务自启动 —— 服务类需要管理员权限,且改动风险高,留给系统自带的"服务管理器" (`services.msc`) 处理。HKLM 与"公共启动文件夹"中的条目在对话框里只读显示,如需启用/禁用,使用 Windows 自带的"任务管理器 → 启动应用"页并以管理员身份运行。

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
git tag v1.1.0
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
├── __main__.py                  # 入口
├── app.py                       # QApplication / HiDPI
├── config.py                    # 读写 %APPDATA% 下的 config.json (含 v1→v4 迁移)
├── autostart.py                 # ShutStart 自身的 HKCU\Run 注册项
├── startup_inventory.py         # 本机启动项枚举 / StartupApproved 软禁用 / 服务类启发式
├── killer.py                    # psutil 终止 A 类进程
├── launcher.py                  # subprocess + ShellExecuteW runas
├── ui/
│   ├── main_dialog.py           # 主对话框 (左右分列)
│   ├── settings_dialog.py       # 设置 (A/B 列表 + 自启 + 主题 + 启动项管理入口)
│   ├── startup_manager_dialog.py # 本机启动项管理对话框 (表格 + 启用/禁用)
│   ├── item_editor.py           # 单项编辑表单
│   └── themes.py                # QSS 主题 (Claude / Mac)
└── resources/                   # 主题图标 (CI 生成)
tools/make_icons.py              # Pillow 程序化生成 ICO
installer/setup.iss              # Inno Setup 脚本
.github/workflows/build.yml      # CI 构建流水线
build.spec                       # PyInstaller spec
version.txt                      # Windows 文件元信息
```

## 卸载

通过"设置 → 应用 → ShutStart → 卸载"。卸载时会:
- 删除安装目录 (`%LocalAppData%\Programs\ShutStart`)
- 清除 HKCU\Run 中的 `ShutStart` 自启项
- **保留** `%APPDATA%\ShutStart\config.json` (用户配置),如需彻底清理可手动删除该目录
