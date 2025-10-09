#!/usr/bin/env python3
"""
Q_DLP 项目代码格式化脚本
使用 autopep8 自动格式化所有 Python 代码文件
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple, Optional


class CodeFormatter:
    """代码格式化工具类"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化格式化工具

        Args:
            project_root: 项目根目录，默认为脚本所在目录
        """
        self.project_root = Path(
            project_root or os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))
        self.python_files = []
        self.excluded_dirs = {
            '.venv',
            '__pycache__',
            '.git',
            '.idea',
            '.vscode',
            'build',
            'dist',
            'temp'}
        self.excluded_files = {'setup.py'}

    def find_python_files(self) -> List[Path]:
        """
        查找项目中所有的Python文件

        Returns:
            Python文件路径列表
        """
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            for file in files:
                if file.endswith('.py') and file not in self.excluded_files:
                    file_path = Path(root) / file
                    python_files.append(file_path)

        return sorted(python_files)

    def check_autopep8_installed(self) -> bool:
        """
        检查 autopep8 是否已安装

        Returns:
            True if installed, False otherwise
        """
        try:
            result = subprocess.run(['autopep8', '--version'],
                                    capture_output=True, text=True, check=True)
            print(f"✅ autopep8 版本: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_autopep8(self) -> bool:
        """
        安装 autopep8

        Returns:
            True if successful, False otherwise
        """
        try:
            print("🔄 正在安装 autopep8...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'autopep8'],
                           check=True)
            print("✅ autopep8 安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ autopep8 安装失败: {e}")
            return False

    def format_file(self, file_path: Path, in_place: bool = True,
                    aggressive: int = 1, max_line_length: int = 88) -> Tuple[bool, str]:
        """
        格式化单个文件

        Args:
            file_path: 文件路径
            in_place: 是否原地修改文件
            aggressive: 激进程度 (0-2)
            max_line_length: 最大行长度

        Returns:
            (success, message) 元组
        """
        try:
            cmd = [
                'autopep8',
                f'--aggressive' if aggressive >= 1 else '',
                f'--aggressive' if aggressive >= 2 else '',
                f'--max-line-length={max_line_length}',
                '--in-place' if in_place else '--diff',
                str(file_path)
            ]

            # 移除空字符串参数
            cmd = [arg for arg in cmd if arg]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            if not in_place and result.stdout:
                return True, f"需要格式化的差异:\n{result.stdout}"
            else:
                return True, "格式化成功"

        except subprocess.CalledProcessError as e:
            return False, f"格式化失败: {e.stderr or e}"

    def format_all_files(self, dry_run: bool = False, aggressive: int = 1,
                         max_line_length: int = 88) -> Tuple[int, int, List[str]]:
        """
        格式化所有Python文件

        Args:
            dry_run: 是否只显示差异而不修改文件
            aggressive: 激进程度
            max_line_length: 最大行长度

        Returns:
            (success_count, total_count, error_messages)
        """
        python_files = self.find_python_files()

        if not python_files:
            print("❌ 未找到Python文件")
            return 0, 0, []

        print(f"📁 找到 {len(python_files)} 个Python文件")
        if dry_run:
            print("🔍 预览模式 - 只显示需要修改的内容，不会修改文件")

        success_count = 0
        error_messages = []

        for i, file_path in enumerate(python_files, 1):
            relative_path = file_path.relative_to(self.project_root)
            print(f"[{i}/{len(python_files)}] 处理: {relative_path}")

            success, message = self.format_file(
                file_path,
                in_place=not dry_run,
                aggressive=aggressive,
                max_line_length=max_line_length
            )

            if success:
                success_count += 1
                if dry_run and "需要格式化的差异:" in message:
                    print(f"  📝 {message}")
                elif not dry_run:
                    print(f"  ✅ {message}")
                else:
                    print("  ✨ 代码格式已符合规范")
            else:
                error_messages.append(f"{relative_path}: {message}")
                print(f"  ❌ {message}")

        return success_count, len(python_files), error_messages

    def check_code_quality(self) -> None:
        """
        检查代码质量统计
        """
        python_files = self.find_python_files()
        total_lines = 0
        total_files = len(python_files)

        print("\n📊 代码统计:")
        print(f"  - Python文件数量: {total_files}")

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
            except Exception:
                pass

        print(f"  - 总代码行数: {total_lines}")
        print(
            f"  - 平均每文件行数: {total_lines // total_files if total_files > 0 else 0}")

    def create_config_file(self) -> None:
        """
        创建 .autopep8 配置文件
        """
        config_path = self.project_root / 'config' / '.autopep8'
        config_content = """[tool:autopep8]
max_line_length = 88
aggressive = 1
in-place = true
recursive = true
exclude = .venv,__pycache__,.git,.idea,.vscode,build,dist,temp
"""

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"✅ 已创建配置文件: {config_path}")
        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Q_DLP 项目代码格式化工具')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='预览模式，只显示差异不修改文件')
    parser.add_argument('--aggressive', '-a', type=int, choices=[0, 1, 2], default=1,
                        help='激进程度 (0=保守, 1=适中, 2=激进)')
    parser.add_argument('--max-line-length', '-l', type=int, default=88,
                        help='最大行长度 (默认: 88)')
    parser.add_argument('--install', action='store_true',
                        help='安装 autopep8')
    parser.add_argument('--config', action='store_true',
                        help='创建 .autopep8 配置文件')
    parser.add_argument('--stats', action='store_true',
                        help='显示代码统计信息')

    args = parser.parse_args()

    # 创建格式化工具实例
    formatter = CodeFormatter()

    print("🐍 Q_DLP 代码格式化工具")
    print("=" * 50)

    # 处理特殊命令
    if args.install:
        if formatter.install_autopep8():
            print("✅ 安装完成，现在可以使用格式化功能")
        return

    if args.config:
        formatter.create_config_file()
        return

    if args.stats:
        formatter.check_code_quality()
        return

    # 检查 autopep8 是否安装
    if not formatter.check_autopep8_installed():
        print("❌ 未找到 autopep8，正在尝试安装...")
        if not formatter.install_autopep8():
            print("💡 请手动安装: pip install autopep8")
            return

    # 执行格式化
    success_count, total_count, errors = formatter.format_all_files(
        dry_run=args.dry_run,
        aggressive=args.aggressive,
        max_line_length=args.max_line_length
    )

    # 显示结果统计
    print("\n" + "=" * 50)
    print("📈 格式化结果:")
    print(f"  - 处理文件数: {total_count}")
    print(f"  - 成功数: {success_count}")
    print(f"  - 失败数: {len(errors)}")

    if errors:
        print("\n❌ 错误列表:")
        for error in errors:
            print(f"  - {error}")

    if args.dry_run:
        print("\n💡 提示: 使用 --dry-run 参数只预览，要实际格式化请去掉此参数")
    else:
        print(f"\n✅ 代码格式化完成！")

    # 显示统计信息
    if total_count > 0:
        formatter.check_code_quality()


if __name__ == "__main__":
    main()
