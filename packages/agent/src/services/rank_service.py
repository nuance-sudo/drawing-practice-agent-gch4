"""ランク管理サービス

ユーザーのデッサンスキルランクを管理し、Firestoreでの永続化を行う。
"""

import uuid
from datetime import datetime

import structlog
from google.cloud import firestore

from src.config import settings
from src.models.rank import RANK_RANGES, Rank, RankHistory, UserRank

logger = structlog.get_logger()


class RankService:
    """ランク管理サービス"""

    USERS_COLLECTION = "users"
    RANK_HISTORY_COLLECTION = "rank_history"

    def __init__(self, db: firestore.Client | None = None) -> None:
        """初期化

        Args:
            db: Firestoreクライアント（テスト用にDI可能）
        """
        if db is None:
            self._db = firestore.Client(
                project=settings.gcp_project_id,
                database=settings.firestore_database,
            )
        else:
            self._db = db
        self._users_collection = self._db.collection(self.USERS_COLLECTION)

    def determine_rank(self, score: float) -> Rank:
        """スコアに基づいてランクを決定する

        Args:
            score: デッサン総合スコア (0-100)

        Returns:
            対応するランク
        """
        # スコアを整数に丸める（四捨五入）か、範囲比較をfloatで行うか。
        # RANK_RANGESはint定義だが、scoreはfloat。
        # ここでは単純な比較を行う。上限については最後のランクでカバーする。
        
        for rank_range in RANK_RANGES:
            if rank_range.min_score <= score <= rank_range.max_score:
                return rank_range.rank
        
        # 範囲外の場合のフォールバック
        if score < 0:
            return Rank.BRONZE
        if score > 100:
            return Rank.DIAMOND
            
        return Rank.BRONZE

    def update_user_rank(self, user_id: str, score: float, task_id: str) -> UserRank:
        """ユーザーのランクを更新する

        最新のスコアに基づいてランクを再計算し、変更があれば履歴を保存する。
        （現在は単純に最新スコア＝ランクとしているが、将来的には移動平均なども検討）

        Args:
            user_id: ユーザーID
            score: 最新のデッサン総合スコア
            task_id: ランク更新のトリガーとなったタスクID

        Returns:
            更新後のユーザーランク情報
        """
        user_ref = self._users_collection.document(user_id)
        
        # トランザクションで実行するのが望ましいが、
        # FirestoreのClientライブラリのトランザクションは使い方が少し複雑なので
        # 今回は簡易的に実装する（厳密な整合性が必須ではないため）
        
        # 1. 現在のユーザー情報を取得
        user_doc = user_ref.get()
        current_rank_val = Rank.BRONZE
        
        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            # 既存のランクがあれば取得
            if "rank" in user_data:
                try:
                    current_rank_val = Rank(user_data["rank"])
                except ValueError:
                    pass

        # 2. 新しいランクを計算
        new_rank_val = self.determine_rank(score)
        now = datetime.now()

        # 3. ユーザー情報を更新（または作成）
        # rankと最新スコアを保存
        update_data = {
            "rank": new_rank_val.value,
            "latest_score": score,
            "updated_at": now,
        }
        
        # マージオプションで保存（他のフィールドを消さないため）
        user_ref.set(update_data, merge=True)

        # 4. ランク変更履歴を保存
        # ランクが変わった場合、または履歴がまだない場合（初回）に保存する方針も考えられるが、
        # 今回は「評価そのもの」がランク判定のイベントなので、毎回履歴に残す形でも良い。
        # ただし、要件では「ランク履歴」なので、ランクが変わった時だけの方がノイズが少ない。
        # ここでは「ランクが変更された場合」および「初回のみ」履歴に残すことにする。
        
        rank_changed = current_rank_val != new_rank_val
        # 初回かどうか判定（user_docが存在しない、またはrankフィールドがない）
        is_first_time = not user_doc.exists or (user_doc.exists and "rank" not in (user_doc.to_dict() or {}))

        if rank_changed or is_first_time:
            history_id = str(uuid.uuid4())
            history_ref = user_ref.collection(self.RANK_HISTORY_COLLECTION).document(history_id)
            
            history_entry = RankHistory(
                user_id=user_id,
                old_rank=None if is_first_time else current_rank_val,
                new_rank=new_rank_val,
                score=score,
                changed_at=now,
                task_id=task_id
            )
            
            history_ref.set({
                "user_id": history_entry.user_id,
                "old_rank": history_entry.old_rank.value if history_entry.old_rank else None,
                "new_rank": history_entry.new_rank.value,
                "score": history_entry.score,
                "changed_at": history_entry.changed_at,
                "task_id": history_entry.task_id
            })
            
            logger.info(
                "rank_updated",
                user_id=user_id,
                old_rank=history_entry.old_rank,
                new_rank=new_rank_val,
                score=score
            )
        else:
            logger.info(
                "rank_unchanged",
                user_id=user_id,
                current_rank=current_rank_val,
                score=score
            )

        return UserRank(
            user_id=user_id,
            current_rank=new_rank_val,
            current_score=score,
            updated_at=now,
        )

    def get_user_rank(self, user_id: str) -> UserRank | None:
        """ユーザーのランク情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            UserRankオブジェクト。ユーザーが存在しない、ランク情報がない場合はNone
        """
        user_ref = self._users_collection.document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
            
        data = user_doc.to_dict() or {}
        if "rank" not in data or "latest_score" not in data:
            return None
            
        try:
            return UserRank(
                user_id=user_id,
                current_rank=Rank(data["rank"]),
                current_score=float(data["latest_score"]),
                updated_at=data.get("updated_at", datetime.now())
            )
        except (ValueError, TypeError):
            logger.warning("invalid_rank_data", user_id=user_id)
            return None


# シングルトンインスタンス
_rank_service: RankService | None = None


def get_rank_service() -> RankService:
    """RankServiceのシングルトンインスタンスを取得"""
    global _rank_service
    if _rank_service is None:
        _rank_service = RankService()
    return _rank_service
