import logging
import os
import random
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union


def get_db_path() -> str:
    """获取数据库文件路径，支持开发环境和打包后环境"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后环境，数据库放在可执行文件目录
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, "download_history.db")
    else:
        # 开发环境，数据库放在项目根目录
        return os.path.join(os.path.dirname(__file__), "download_history.db")


DB_PATH = get_db_path()


@contextmanager
def get_db_connection():
    """数据库连接上下文管理器，确保连接正确关闭"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logging.error(f"数据库操作失败: {e}")
        raise
    finally:
        if conn:
            conn.close()


def _check_table_exists(cursor, table_name: str) -> bool:
    """检查表是否存在"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def _get_table_columns(cursor, table_name: str) -> List[str]:
    """获取表的所有列名"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [column[1] for column in cursor.fetchall()]


def _migrate_database(conn) -> bool:
    """迁移数据库结构到最新版本"""
    cursor = conn.cursor()

    try:
        # 检查是否需要添加新列
        if _check_table_exists(cursor, 'downloads'):
            existing_columns = _get_table_columns(cursor, 'downloads')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 添加缺失的列（使用常量默认值）
            if 'created_at' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE downloads 
                    ADD COLUMN created_at TEXT DEFAULT ''
                """)
                # 更新现有记录的created_at值
                cursor.execute("""
                    UPDATE downloads 
                    SET created_at = ? 
                    WHERE created_at = '' OR created_at IS NULL
                """, (current_time,))
                logging.info("添加 created_at 列")

            if 'updated_at' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE downloads 
                    ADD COLUMN updated_at TEXT DEFAULT ''
                """)
                # 更新现有记录的updated_at值
                cursor.execute("""
                    UPDATE downloads 
                    SET updated_at = ? 
                    WHERE updated_at = '' OR updated_at IS NULL
                """, (current_time,))
                logging.info("添加 updated_at 列")

        conn.commit()
        return True
    except Exception as e:
        logging.error(f"数据库迁移失败: {e}")
        return False


def init_db() -> bool:
    """初始化数据库，创建表结构"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 创建表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    file_path TEXT DEFAULT '',
                    platform TEXT DEFAULT '',
                    download_time TEXT DEFAULT '',
                    is_finished BOOLEAN DEFAULT 0
                )
            """)

            # 迁移数据库结构
            if not _migrate_database(conn):
                return False

            # 创建索引（如果不存在）
            try:
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_downloads_url_unique ON downloads(url)
                """)
            except sqlite3.IntegrityError:
                # 如果已存在重复URL，先清理重复项
                logging.warning("检测到重复URL，正在清理...")
                cursor.execute("""
                    DELETE FROM downloads 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM downloads 
                        GROUP BY url
                    )
                """)
                # 重新尝试创建索引
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_downloads_url_unique ON downloads(url)
                """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_platform ON downloads(platform)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_finished ON downloads(is_finished)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_created_at ON downloads(created_at)
            """)

            conn.commit()
            logging.info("数据库初始化成功")
            return True
    except Exception as e:
        logging.error(f"数据库初始化失败: {e}")
        return False


def insert_download(url: str, title: str = "", file_path: str = "",
                    platform: str = "", is_finished: bool = False) -> Optional[int]:
    """插入下载记录到数据库"""
    if not url or not url.strip():
        logging.error("URL不能为空")
        return None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO downloads 
                (url, title, file_path, platform, download_time, is_finished, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                url.strip(),
                title.strip(),
                file_path.strip(),
                platform.strip(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                is_finished,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            record_id = cursor.lastrowid
            logging.info(f"插入下载记录成功，ID: {record_id}")
            return record_id
    except Exception as e:
        logging.error(f"插入下载记录失败: {e}")
        return None


def update_download_status(url: str, is_finished: bool, file_path: str = "") -> bool:
    """更新下载状态"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE downloads 
                SET is_finished = ?, file_path = ?, updated_at = ?
                WHERE url = ?
            """, (is_finished, file_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url))
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"更新下载状态成功: {url}")
                return True
            else:
                logging.warning(f"未找到要更新的记录: {url}")
                return False
    except Exception as e:
        logging.error(f"更新下载状态失败: {e}")
        return False


def delete_download_record(record_id: int) -> bool:
    """删除指定的下载记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM downloads WHERE id = ?", (record_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"删除下载记录成功，ID: {record_id}")
                return True
            else:
                logging.warning(f"未找到要删除的记录，ID: {record_id}")
                return False
    except Exception as e:
        logging.error(f"删除下载记录失败: {e}")
        return False


def clear_downloads_at_db() -> bool:
    """清空所有下载记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM downloads")
            conn.commit()
            logging.info(f"清空下载记录成功，共删除 {cursor.rowcount} 条记录")
            return True
    except Exception as e:
        logging.error(f"清空下载记录失败: {e}")
        return False


_char_set = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_id(length: int = 8) -> str:
    """生成一个指定长度的随机ID"""
    return ''.join(random.choice(_char_set) for _ in range(length))


@dataclass
class DownloadRecord:
    """下载记录数据类"""
    id: int
    url: str
    title: str = ""
    file_path: str = ""
    platform: str = ""
    time: str = ""  # download_time
    is_finished: bool = False
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_db_row(cls, row) -> 'DownloadRecord':
        """从数据库行创建DownloadRecord实例"""
        return cls(
            id=row['id'],
            url=row['url'],
            title=row['title'] or "",
            file_path=row['file_path'] or "",
            platform=row['platform'] or "",
            time=row['download_time'] or "",
            is_finished=bool(row['is_finished']),
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or ""
        )

    def insert_to_db(self) -> Optional[int]:
        """将记录插入数据库"""
        return insert_download(
            self.url,
            self.title,
            self.file_path,
            self.platform,
            self.is_finished
        )

    def update_status(self, is_finished: bool, file_path: str = "") -> bool:
        """更新下载状态"""
        result = update_download_status(self.url, is_finished, file_path)
        if result:
            self.is_finished = is_finished
            if file_path:
                self.file_path = file_path
        return result

    def delete(self) -> bool:
        """删除当前记录"""
        return delete_download_record(self.id)


def get_all_downloads_at_db() -> List[DownloadRecord]:
    """获取所有下载记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [DownloadRecord.from_db_row(row) for row in rows]
    except Exception as e:
        logging.error(f"获取下载记录失败: {e}")
        return []


def get_downloads_by_platform(platform: str) -> List[DownloadRecord]:
    """根据平台获取下载记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE platform = ? ORDER BY created_at DESC",
                (platform,)
            )
            rows = cursor.fetchall()
            return [DownloadRecord.from_db_row(row) for row in rows]
    except Exception as e:
        logging.error(f"获取平台下载记录失败: {e}")
        return []


def get_finished_downloads() -> List[DownloadRecord]:
    """获取已完成的下载记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE is_finished = 1 ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
            return [DownloadRecord.from_db_row(row) for row in rows]
    except Exception as e:
        logging.error(f"获取完成下载记录失败: {e}")
        return []


def get_unfinished_downloads() -> List[DownloadRecord]:
    """获取未完成的下载记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE is_finished = 0 ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [DownloadRecord.from_db_row(row) for row in rows]
    except Exception as e:
        logging.error(f"获取未完成下载记录失败: {e}")
        return []


def search_downloads(keyword: str) -> List[DownloadRecord]:
    """搜索下载记录"""
    if not keyword or not keyword.strip():
        return []

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{keyword.strip()}%"
            cursor.execute("""
                SELECT * FROM downloads 
                WHERE title LIKE ? OR url LIKE ? OR platform LIKE ?
                ORDER BY created_at DESC
            """, (search_term, search_term, search_term))
            rows = cursor.fetchall()
            return [DownloadRecord.from_db_row(row) for row in rows]
    except Exception as e:
        logging.error(f"搜索下载记录失败: {e}")
        return []


def get_download_stats() -> dict:
    """获取下载统计信息"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 总数
            cursor.execute("SELECT COUNT(*) FROM downloads")
            total_count = cursor.fetchone()[0]

            # 完成数
            cursor.execute(
                "SELECT COUNT(*) FROM downloads WHERE is_finished = 1")
            finished_count = cursor.fetchone()[0]

            # 各平台统计
            cursor.execute("""
                SELECT platform, COUNT(*) 
                FROM downloads 
                WHERE platform != '' 
                GROUP BY platform
            """)
            platform_stats = dict(cursor.fetchall())

            return {
                'total_count': total_count,
                'finished_count': finished_count,
                'unfinished_count': total_count - finished_count,
                'platform_stats': platform_stats,
                'success_rate': (finished_count / total_count * 100) if total_count > 0 else 0
            }
    except Exception as e:
        logging.error(f"获取下载统计失败: {e}")
        return {
            'total_count': 0,
            'finished_count': 0,
            'unfinished_count': 0,
            'platform_stats': {},
            'success_rate': 0
        }


def _insert_test_data() -> bool:
    """插入测试数据"""
    test_data = [
        {
            'url': "https://example.com/video1",
            'title': "测试视频1",
            'platform': "YouTube",
            'is_finished': True,
            'file_path': "/path/to/video1.mp4"
        },
        {
            'url': "https://example.com/video2",
            'title': "测试视频2",
            'platform': "Bilibili",
            'is_finished': False
        },
        {
            'url': "https://example.com/video3",
            'title': "测试视频3",
            'platform': "YouTube",
            'is_finished': True,
            'file_path': "/path/to/video3.mp4"
        }
    ]

    success_count = 0
    for data in test_data:
        if insert_download(**data):
            success_count += 1

    logging.info(f"插入测试数据完成，成功 {success_count}/{len(test_data)} 条")
    return success_count == len(test_data)


def backup_database(backup_path: Optional[str] = None) -> bool:
    """备份数据库"""
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"download_history_backup_{timestamp}.db"

    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        logging.info(f"数据库备份成功: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"数据库备份失败: {e}")
        return False


def restore_database(backup_path: str) -> bool:
    """从备份恢复数据库"""
    if not os.path.exists(backup_path):
        logging.error(f"备份文件不存在: {backup_path}")
        return False

    try:
        import shutil
        shutil.copy2(backup_path, DB_PATH)
        logging.info(f"数据库恢复成功: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"数据库恢复失败: {e}")
        return False


def optimize_database() -> bool:
    """优化数据库（清理碎片、重建索引）"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("REINDEX")
            conn.commit()
            logging.info("数据库优化完成")
            return True
    except Exception as e:
        logging.error(f"数据库优化失败: {e}")
        return False


if __name__ == '__main__':
    # 初始化数据库
    if init_db():
        print("数据库初始化成功")

        # 显示统计信息
        stats = get_download_stats()
        print(f"数据库统计: {stats}")

        # 如果是测试环境，可以插入测试数据
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            print("插入测试数据...")
            _insert_test_data()

            # 显示所有记录
            records = get_all_downloads_at_db()
            print(f"总记录数: {len(records)}")
            for record in records:
                print(
                    f"  - {record.title} ({record.platform}) - {'完成' if record.is_finished else '未完成'}")
    else:
        print("数据库初始化失败")
