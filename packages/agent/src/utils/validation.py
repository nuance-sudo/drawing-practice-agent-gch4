"""URL検証ユーティリティ

SSRF対策のためのURL検証機能を提供。
"""

import ipaddress
import re
from urllib.parse import unquote, urlparse

from src.config import settings
from src.exceptions import ImageProcessingError

# 許可するホスト名（完全一致）
ALLOWED_HOSTNAMES = [
    "storage.googleapis.com",
    "storage.cloud.google.com",
]

# 許可するGCSバケット名（gs://スキーム用）
# 設定から読み込むか、ここでハードコード
ALLOWED_GCS_BUCKETS = [
    # プロジェクト固有のバケット名をここに追加
    # 例: "my-project-images"
]

# 禁止するIPレンジ（プライベートIP、メタデータエンドポイント等）
BLOCKED_IP_RANGES_V4 = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # メタデータエンドポイント
    ipaddress.ip_network("0.0.0.0/8"),
]

# IPv6ブロックリスト
BLOCKED_IP_RANGES_V6 = [
    ipaddress.ip_network("::1/128"),  # Localhost
    ipaddress.ip_network("fe80::/10"),  # Link-local
    ipaddress.ip_network("::ffff:0:0/96"),  # IPv4-mapped
    ipaddress.ip_network("fc00::/7"),  # Unique local
    ipaddress.ip_network("ff00::/8"),  # Multicast
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

    # URLデコードして正規化
    normalized_url = unquote(url)

    # スキームを確認
    parsed = urlparse(normalized_url)
    if parsed.scheme not in ("https", "gs"):
        raise ImageProcessingError(f"許可されていないスキームです: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ImageProcessingError("ホスト名が取得できません")

    # IPアドレス形式の場合はブロックリストを確認
    try:
        ip = ipaddress.ip_address(hostname)
        blocked_ranges = BLOCKED_IP_RANGES_V6 if ip.version == 6 else BLOCKED_IP_RANGES_V4
        for blocked_range in blocked_ranges:
            if ip in blocked_range:
                raise ImageProcessingError(
                    f"プライベートIPへのアクセスは許可されていません: {hostname}"
                )
        # IPアドレス直接指定は許可しない
        raise ImageProcessingError("IPアドレス直接指定は許可されていません")
    except ValueError:
        # ホスト名の場合は完全一致で検証
        pass

    # gs:// スキームの場合はバケット名を検証
    if parsed.scheme == "gs":
        bucket_name = parsed.netloc  # gs://bucket-name/path → bucket-name

        # 設定からバケット許可リストを取得
        allowed_buckets = ALLOWED_GCS_BUCKETS.copy()
        if settings.gcs_bucket_name:
            allowed_buckets.append(settings.gcs_bucket_name)

        if not allowed_buckets:
            # 許可リストが空の場合はエラー（本番環境では必須）
            raise ImageProcessingError(
                "GCSバケット許可リストが設定されていません。"
                "GCS_BUCKET_NAME環境変数を設定してください。"
            )

        if bucket_name not in allowed_buckets:
            raise ImageProcessingError(f"許可されていないGCSバケットです: {bucket_name}")
        return normalized_url

    # ホスト名の完全一致を確認
    is_allowed = hostname in ALLOWED_HOSTNAMES

    # 設定されたCDN URLのホスト名も許可
    if settings.cdn_base_url:
        cdn_parsed = urlparse(settings.cdn_base_url)
        if cdn_parsed.hostname and hostname == cdn_parsed.hostname:
            is_allowed = True

    if not is_allowed:
        raise ImageProcessingError(
            f"許可されていないホストです: {hostname}。Cloud StorageまたはCDN URLのみ使用可能です"
        )

    return normalized_url


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
