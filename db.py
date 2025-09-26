import logging
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime

DB_PATH = "download_history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS downloads
                   (
                       id
                           INTEGER
                           PRIMARY
                               KEY,
                       url
                           TEXT
                           NOT
                               NULL,
                       title
                           TEXT,
                       file_path
                           TEXT,
                       platform
                           TEXT,
                       download_time
                           TEXT,
                       is_finished
                           BOOLEAN
                           DEFAULT 0
                   )
                   """)
    conn.commit()
    conn.close()

    logging.info("Database initialized")


def insert_download(url, title, file_path, platform, is_finished=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO downloads (url, title, file_path, platform, download_time, is_finished)
                   VALUES (?, ?, ?, ?, ?, ?)
                   """, (url, title, file_path, platform, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), is_finished))
    conn.commit()
    conn.close()


def clear_downloads_at_db():
    """清空下载记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM downloads")
    conn.commit()
    conn.close()

    logging.info("Database cleared")


_char_set = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_id(length=8):
    """生成一个指定长度的随机ID"""
    return ''.join(random.choice(_char_set) for _ in range(length))


@dataclass
class DownloadRecord:
    id: int
    url: str
    title: str = ""
    file_path: str = ""
    platform: str = ""
    time: str = ""
    is_finished: bool = False

    def insert_to_db(self):
        insert_download(self.url, self.title, self.file_path, self.platform)


def get_all_downloads_at_db() -> list[DownloadRecord]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM downloads ORDER BY id DESC")
    results = cursor.fetchall()
    conn.close()
    return [DownloadRecord(*row) for row in map(lambda x: (*x[:-1], bool(x[-1])), results)]


def _insert_test_data():
    _test_downloads_data = [
        DownloadRecord(id=1, url="https://example.com/video1", title="Video 1", file_path="/path/to/video1.mp4",
                       platform="YouTube", time="2023-10-01 12:00:00", is_finished=True),
        DownloadRecord(id=2, url="https://example.com/video2", title="Video 2", file_path="/path/to/video2.mp4",
                       platform="YouTube", time="2023-10-02 13:00:00", is_finished=False),
        DownloadRecord(id=3, url="https://example.com/video3", title="Video 3", file_path="/path/to/video3.mp4",
                       platform="Bilibili", time="2023-10-03 14:00:00", is_finished=True),
        DownloadRecord(id=4, url="https://example.com/video4", title="Video 4", file_path="/path/to/video4.mp4",
                       platform="Bilibili", time="2023-10-04 15:00:00", is_finished=False),
        DownloadRecord(id=5, url="https://example.com/video5", title="Video 5", file_path="/path/to/video5.mp4",
                       platform="YouTube", time="2023-10-05 16:00:00", is_finished=True),
    ]
    for record in _test_downloads_data:
        record.insert_to_db()


if __name__ == '__main__':
    clear_downloads_at_db()
