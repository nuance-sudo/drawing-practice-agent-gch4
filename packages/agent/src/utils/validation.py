"""URL検証ユーティリティ

SSRF対策のためのURL検証機能を提供。
"""

import ipaddress
import re
from urllib.parse import urlparse

from src.config import settings
from src.exceptions import ImageProcessingError

# 許可するCloud Storageバケットパターン
ALLOWED_GCS_PATTERNS = [
    r"^https://storage\.googleapis\.com/.+$",
    r"^https://storage\.cloud\.google\.com/.+$",
    r"^gs://.+$",
]

# 禁止するIPレンジ（プライベートIP、メタデータエンドポイント等）
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # メタデータエンドポイント
    ipaddress.ip_network("0.0.0.0/8"),
]


def validate_image_url(url: str) -> str:
    """画像URLを検証しSSRF攻撃を防止

    Args:
        url: 検証する画像URL

    Returns:
        検証済みのURL

    Raises:
        ImageProcessingError: URLが無効な場合
    """
    if not url:
        raise ImageProcessingError("画像URLが空です")

    # スキームを確認
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "gs"):
        raise ImageProcessingError(f"許可されていないスキームです: {parsed.scheme}")

    # ホスト名からIPアドレスを解決してブロックリストを確認
    hostname = parsed.hostname
    if hostname:
        # IPアドレス形式の場合は直接チェック
        try:
            ip = ipaddress.ip_address(hostname)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    raise ImageProcessingError(
                        f"プライベートIPへのアクセスは許可されていません: {hostname}"
                    )
        except ValueError:
            # ホスト名の場合はパターンマッチ
            pass

    # Cloud Storage URLパターンを検証
    is_allowed = False
    for pattern in ALLOWED_GCS_PATTERNS:
        if re.match(pattern, url):
            is_allowed = True
            break

    # 設定されたCDN URLも許可
    if settings.cdn_base_url and url.startswith(settings.cdn_base_url):
        is_allowed = True

    if not is_allowed:
        raise ImageProcessingError(
            f"許可されていないURLです。Cloud StorageまたはCDN URLのみ使用可能です: {url}"
        )

    return url


def sanitize_for_storage(text: str, max_length: int = 10000) -> str:
    """テキストをストレージ用にサニタイズ

    Args:
        text: サニタイズするテキスト
        max_length: 最大文字数

    Returns:
        サニタイズ済みテキスト
    """
    if not text:
        return ""

    # 長さ制限
    sanitized = text[:max_length]

    # 制御文字を除去（改行・タブは許可）
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

    return sanitized
