# Claude Dashboard - 快速开始

## 一分钟安装

### 步骤 1：运行安装脚本

在项目根目录执行：

```bash
python3 scripts/install.sh
```

这会注册本地 marketplace 到 Claude Code 配置中。

### 步骤 2：安装插件

重启 Claude Code（如果正在运行），然后运行：

```
/plugins install claude-dashboard-local
```

### 步骤 3：启动 Claude Code

```bash
claude
```

启动后你应该看到类似以下的输出：

```
╔══════════════════════════════════════════════════════════╗
║  📊  Claude Dashboard Ready                              ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Open in your browser to view session data:              ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │ http://127.0.0.1:18080/?session_id=xxx             │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

### 步骤 4：访问 Dashboard

点击终端中显示的链接，在浏览器中打开即可看到 Dashboard 界面。

## 功能一览

### Token 统计
- 实时追踪输入/输出/工具调用 token
- 可视化上下文窗口占用情况
- 按会话、日期统计汇总

### 配置管理
- Skills 管理：增删改查、启用/禁用
- MCP 服务管理：配置管理、连通性测试
- 插件管理：安装、卸载、启用/禁用

### 会话历史
- 查看所有对话记录
- 搜索、筛选、导出

### 会话隔离
- 每个 Claude Code CLI 窗口自动注册会话
- 直接链接访问：`http://127.0.0.1:18080/?session_id=xxx`
- 会话隔离 - 只看当前会话的数据
- 无需手动选择会话

## 常见问题

### Q: 没有看到 Dashboard 链接？

**A:** 确认插件已正确安装：
```
/plugins list
```

如果未列出，重新安装：
```
/plugins install claude-dashboard-local
```

### Q: 链接打不开？

**A:** Backend 服务可能未启动。手动启动：
```bash
cd backend
python main.py
```

### Q: 如何卸载？

**A:** 运行以下命令卸载插件：
```
/plugins uninstall claude-dashboard-local
```

## 文档

- [插件架构](./PLUGIN_ARCHITECTURE.md) - 详细的插件结构和 hooks 机制
- [项目结构](./STRUCTURE.md) - 完整的目录结构说明
- [安装指南](./INSTALL.md) - 详细的安装和故障排除

## 开发

### 修改 Hooks 代码

1. 修改 `hooks/*.py` 文件
2. 重启 Claude Code
3. Hooks 会自动重新加载

### 修改 Backend 代码

1. 修改 `backend/*.py` 文件
2. 重启 backend 服务
3. 刷新浏览器

### 修改 Frontend 代码

```bash
cd frontend
npm install
npm run dev
```

然后在浏览器中访问开发服务器地址。

---

**需要帮助？** 查看 [INSTALL.md](./INSTALL.md) 获取详细的故障排除指南。
