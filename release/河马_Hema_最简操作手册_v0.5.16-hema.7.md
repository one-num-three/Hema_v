# 河马 Hema 最简操作手册

适用版本：`v0.5.16-hema.7`

## 1. 下载

从 Release 页面下载全量包：

`Hema_v-v0.5.16-hema.7-full-local.zip`

不要使用 `v0.5.16-hema.6`，那个包缺少 Python 标准库文件。

## 2. 解压

把 zip 解压到一个固定目录，例如：

`F:\hema-fix`

建议不要解压到微信临时目录、浏览器下载临时目录或系统盘深层目录。

## 3. 安装

进入解压后的文件夹，双击：

`installer_gui.bat`

推荐选择：

- 安装路径：`F:\hema-fix` 或你想安装的位置
- 安装模式：完整安装
- 创建桌面快捷方式：勾选

安装完成后，桌面会出现快捷方式。

## 4. 启动

优先双击桌面快捷方式：

`河马 Web 管理界面`

它会自动启动：

- 河马网关
- Web UI 管理界面
- 浏览器页面

正常打开后，浏览器地址一般是：

`http://localhost:8648/`

不需要再手动点一次“河马网关”。

如果提示输入token，随便输入即可进入。

## 5. 停止

如果需要关闭 Web UI，双击或运行：

`stop_webui.bat`

如果只是关闭浏览器页面，后台服务可能仍在运行。

## 6. 卸载

进入安装目录，双击：

`uninstall.bat`

卸载会清理启动文件和快捷方式。

如果你还想删除聊天记录、记忆、skills，需要手动检查：

`C:\Users\你的用户名\.hermes`

不确定就先不要删。

## 7. Skills 放在哪里

Hermes 正式使用的 skills 在：

`C:\Users\你的用户名\.hermes\skills`

例如：

`C:\Users\你的用户名\.hermes\skills\productivity\ppt-master`

如果你在 `F:\hema-fix\ppt-master` 看到一个完整仓库，那通常是 Hermes 在本地工作目录下载/克隆出来的临时项目，不是正式 skill 目录。

删除前请先确认里面有没有你生成的 PPT 或项目文件。

## 8. 常见问题

### 页面显示“未连接”

请关闭浏览器，然后重新双击：

`河马 Web 管理界面`

新版会自动检查并启动网关。

### 出现 Python encodings 报错

请确认你使用的是：

`v0.5.16-hema.7`

不要使用：

`v0.5.16-hema.6`

### Windows 提示“不安全下载”

这是因为安装包没有代码签名，或者下载地址不是 HTTPS。

只要你是从自己的 GitHub Release 下载，并且校验 sha256 一致，就可以继续使用。

### 中转站打不开或跳错地址

新版中转站地址是：

`https://ai.opcstore.com/login?expired=true`

如果还是旧地址，请重新安装 `v0.5.16-hema.7`。

## 9. 最推荐流程

1. 下载 `Hema_v-v0.5.16-hema.7-full-local.zip`
2. 解压到 `F:\hema-fix`
3. 双击 `installer_gui.bat`
4. 安装完成后双击桌面 `河马 Web 管理界面`
5. 浏览器打开后直接聊天

