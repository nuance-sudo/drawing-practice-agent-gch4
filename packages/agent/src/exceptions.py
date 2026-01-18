"""カスタム例外定義"""


class DessinCoachingError(Exception):
    """ベース例外クラス"""

    pass


class TaskNotFoundError(DessinCoachingError):
    """タスクが見つからない場合の例外"""

    pass


class AnalysisFailedError(DessinCoachingError):
    """デッサン分析が失敗した場合の例外"""

    pass


class ImageProcessingError(DessinCoachingError):
    """画像処理が失敗した場合の例外"""

    pass


class StorageError(DessinCoachingError):
    """ストレージ操作が失敗した場合の例外"""

    pass


class GeminiAPIError(DessinCoachingError):
    """Gemini API呼び出しが失敗した場合の例外"""

    pass
