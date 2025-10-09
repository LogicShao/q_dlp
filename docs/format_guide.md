# 代码格式化工具使用指南

## 📋 概述

本项目提供了多种方式来自动格式化Python代码，使用`autopep8`工具确保代码符合PEP 8标准。

## 🛠️ 工具列表

### 1. Python脚本 (推荐)
- **文件**: `format_code.py`
- **功能**: 功能最全面的格式化工具
- **平台**: 跨平台支持

### 2. Windows批处理脚本
- **文件**: `format_code.bat`
- **功能**: Windows系统便捷使用
- **平台**: Windows

### 3. Linux/Mac Shell脚本
- **文件**: `format_code.sh`
- **功能**: Unix系统便捷使用
- **平台**: Linux/Mac

### 4. Makefile命令
- **文件**: `Makefile`
- **功能**: 标准化的开发命令
- **平台**: 支持make的系统

## 🚀 快速开始

### 方法一：使用Python脚本 (推荐)

```bash
# 1. 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. 格式化所有代码
python format_code.py

# 3. 预览模式（不修改文件）
python format_code.py --dry-run

# 4. 安装autopep8
python format_code.py --install

# 5. 显示代码统计
python format_code.py --stats
```

### 方法二：使用批处理/Shell脚本

```bash
# Windows
format_code.bat

# Linux/Mac
chmod +x format_code.sh
./format_code.sh
```

### 方法三：使用Makefile

```bash
# 格式化代码
make format

# 检查格式（预览模式）
make format-check

# 显示统计信息
make stats

# 查看所有可用命令
make help
```

## ⚙️ 配置选项

### 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--dry-run` | `-d` | 预览模式，不修改文件 |
| `--aggressive` | `-a` | 激进程度 (0-2) |
| `--max-line-length` | `-l` | 最大行长度 |
| `--install` | - | 安装autopep8 |
| `--config` | - | 创建配置文件 |
| `--stats` | - | 显示代码统计 |
| `--help` | `-h` | 显示帮助信息 |

### 配置文件

项目包含 `.autopep8` 配置文件：

```ini
[tool:autopep8]
max_line_length = 88
aggressive = 1
in-place = true
recursive = true
exclude = .venv,__pycache__,.git,.idea,.vscode,build,dist,temp
```

## 📝 使用示例

### 基本格式化

```bash
# 格式化所有Python文件
python format_code.py

# 输出示例
🐍 Q_DLP 代码格式化工具
==================================================
✅ autopep8 版本: autopep8 2.0.4
📁 找到 8 个Python文件
[1/8] 处理: main.py
  ✅ 格式化成功
[2/8] 处理: MainWindow.py
  ✅ 格式化成功
...
✅ 代码格式化完成！
```

### 预览模式

```bash
# 查看需要修改的内容但不实际修改
python format_code.py --dry-run

# 输出示例
🔍 预览模式 - 只显示需要修改的内容，不会修改文件
[1/8] 处理: main.py
  ✨ 代码格式已符合规范
[2/8] 处理: db.py
  📝 需要格式化的差异:
--- original/db.py
+++ fixed/db.py
@@ -10,7 +10,7 @@
-def   init_db():
+def init_db():
```

### 自定义参数

```bash
# 使用激进模式和120字符行长度
python format_code.py --aggressive 2 --max-line-length 120

# 只预览，使用保守模式
python format_code.py --dry-run --aggressive 0
```

### 代码统计

```bash
python format_code.py --stats

# 输出示例
📊 代码统计:
  - Python文件数量: 8
  - 总代码行数: 1247
  - 平均每文件行数: 155
```

## 🔧 高级功能

### 1. 批量处理

脚本会自动发现并处理项目中所有Python文件，排除以下目录：
- `.venv` - 虚拟环境
- `__pycache__` - Python缓存
- `.git` - Git目录
- `.idea` - PyCharm配置
- `.vscode` - VS Code配置
- `build` - 构建目录
- `dist` - 分发目录
- `temp` - 临时文件

### 2. 错误处理

脚本提供完整的错误处理和报告：

```bash
📈 格式化结果:
  - 处理文件数: 8
  - 成功数: 7
  - 失败数: 1

❌ 错误列表:
  - db.py: 格式化失败: [Errno 13] Permission denied
```

### 3. 自动安装依赖

如果系统中没有安装`autopep8`，脚本会自动尝试安装：

```bash
❌ 未找到 autopep8，正在尝试安装...
🔄 正在安装 autopep8...
✅ autopep8 安装成功
```

## 📋 最佳实践

### 1. 开发流程集成

建议将代码格式化集成到开发流程中：

```bash
# 开发前检查
make format-check

# 提交前格式化
make format

# 完整质量检查
make quality  # 等同于 format + lint
```

### 2. 预提交钩子

可以设置Git预提交钩子自动格式化：

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "🔄 运行代码格式化..."
python format_code.py --dry-run
if [ $? -ne 0 ]; then
    echo "❌ 代码格式检查失败，请运行: python format_code.py"
    exit 1
fi
```

### 3. CI/CD集成

在持续集成中检查代码格式：

```yaml
# .github/workflows/code-quality.yml
- name: Check code format
  run: |
    pip install autopep8
    python format_code.py --dry-run
```

## ⚠️ 注意事项

### 1. 备份重要代码

虽然工具经过测试，但建议在格式化前：
- 提交当前更改到Git
- 或创建代码备份

### 2. 激进模式谨慎使用

`--aggressive 2` 可能会改变代码逻辑：

```python
# 原代码
if x == True:  # 可能有特定用意
    pass

# 激进模式格式化后
if x:  # 逻辑可能改变
    pass
```

### 3. 大型项目处理

对于大型项目：
- 先使用 `--dry-run` 预览
- 分批处理重要文件
- 及时测试格式化后的代码

## 🐛 故障排除

### 常见问题

1. **权限错误**
   ```bash
   # 解决方案：检查文件权限
   chmod 644 *.py
   ```

2. **虚拟环境问题**
   ```bash
   # 解决方案：重新创建虚拟环境
   rm -rf .venv
   python -m venv .venv
   ```

3. **autopep8安装失败**
   ```bash
   # 解决方案：手动安装
   pip install --upgrade pip
   pip install autopep8
   ```

4. **编码错误**
   ```bash
   # 解决方案：检查文件编码
   file --mime-encoding *.py
   ```

### 获取帮助

```bash
# 查看详细帮助
python format_code.py --help

# 查看Makefile命令
make help

# 检查autopep8版本
autopep8 --version
```

---

*最后更新：2025年9月28日*