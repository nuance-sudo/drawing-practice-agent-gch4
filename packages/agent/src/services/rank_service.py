"""ランク管理サービス

ユーザーのデッサンスキルランクを管理し、Firestoreでの永続化を行う。
"""

import uuid
from datetime import datetime
from typing import List

import structlog
from google.cloud import firestore

from src.config import settings
from src.models.rank import Rank, RankHistory, UserRank

logger = structlog.get_logger()


class RankService:
    """ランク管理サービス"""

    USERS_COLLECTION = "users"
    RANK_HISTORY_COLLECTION = "rank_history"
    
    # ランク昇格に必要な「80点以上の獲得回数」定義
    # 累積回数で判定する
    # 10級(Level 1)は初期ランク
    RANK_CRITERIA = {
        Rank.KYU_9: 1,
        Rank.KYU_8: 2,
        Rank.KYU_7: 3,
        Rank.KYU_6: 4,
        Rank.KYU_5: 5,
        Rank.KYU_4: 6,
        Rank.KYU_3: 7,
        Rank.KYU_2: 8,
        Rank.KYU_1: 10,
        Rank.DAN_1: 12,
        Rank.DAN_2: 15,
        Rank.DAN_3: 20,
        Rank.SHIHAN_DAI: 25,
        Rank.SHIHAN: 30,
    }

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

    def calculate_rank(self, high_score_count: int) -> Rank:
        """高スコア獲得回数に基づいてランクを計算する

        Args:
            high_score_count: 80点以上のを獲得した回数

        Returns:
            対応するランク
        """
        # 条件を満たす最大のランクを探す
        # 降順（師範 -> 9級）でチェックし、最初に見つかった基準を満たすものを選ぶ
        sorted_criteria = sorted(self.RANK_CRITERIA.items(), key=lambda x: x[0], reverse=True)
        
        for rank, required_count in sorted_criteria:
            if high_score_count >= required_count:
                return rank
        
        # 基準に満たない場合は10級
        return Rank.KYU_10

    def update_user_rank(self, user_id: str, score: float, task_id: str) -> UserRank:
        """ユーザーのランクを更新する

        最新のスコアに基づいて情報を更新し、ランク再計算を行う。
        80点以上のスコアを獲得した場合、カウントが増加し昇格の可能性がある。

        Args:
            user_id: ユーザーID
            score: 最新のデッサン総合スコア
            task_id: ランク更新のトリガーとなったタスクID

        Returns:
            更新後のユーザーランク情報
        """
        user_ref = self._users_collection.document(user_id)
        
        # 1. 現在のユーザー情報を取得
        user_doc = user_ref.get()
        current_rank = Rank.KYU_10
        total_submissions = 0
        high_scores = []
        
        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            # 既存のランク情報があれば取得
            if "rank" in user_data:
                try:
                    current_rank = Rank(user_data["rank"])
                except ValueError:
                    current_rank = Rank.KYU_10
            
            total_submissions = user_data.get("total_submissions", 0)
            high_scores = user_data.get("high_scores", [])

        # 2. 新しい情報を追加
        total_submissions += 1
        
        # 80点以上なら高スコアリストに追加
        if score >= 80:
            high_scores.append(score)
            
        # 3. 新しいランクを計算
        new_rank = self.calculate_rank(len(high_scores))
        now = datetime.now()

        # 4. ユーザー情報を更新
        update_data = {
            "rank": new_rank.value,
            "latest_score": score,
            "total_submissions": total_submissions,
            "high_scores": high_scores,
            "updated_at": now,
        }
        
        # マージオプションで保存
        user_ref.set(update_data, merge=True)

        rank_changed = current_rank != new_rank
        # 初回登録かどうかの判定 (docがない、またはrankがない)
        is_first_time = not user_doc.exists or (user_doc.exists and "rank" not in (user_doc.to_dict() or {}))

        # 5. ランク変更履歴を保存 (変更時または初回)
        if rank_changed or is_first_time:
            history_id = str(uuid.uuid4())
            history_ref = user_ref.collection(self.RANK_HISTORY_COLLECTION).document(history_id)
            
            history_entry = RankHistory(
                user_id=user_id,
                old_rank=None if is_first_time else current_rank,
                new_rank=new_rank,
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
            
            if rank_changed:
                logger.info(
                    "rank_promoted",
                    user_id=user_id,
                    old_rank=current_rank.label,
                    new_rank=new_rank.label,
                    score=score
                )
        else:
            logger.info(
                "rank_unchanged",
                user_id=user_id,
                current_rank=current_rank.label,
                score=score
            )

        return UserRank(
            user_id=user_id,
            current_rank=new_rank,
            current_score=score,
            total_submissions=total_submissions,
            high_scores=high_scores,
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
        if "rank" not in data:
            return None
            
        try:
            return UserRank(
                user_id=user_id,
                current_rank=Rank(data["rank"]),
                current_score=float(data.get("latest_score", 0)),
                total_submissions=int(data.get("total_submissions", 0)),
                high_scores=data.get("high_scores", []),
                updated_at=data.get("updated_at", datetime.now())
            )
        except (ValueError, TypeError) as e:
            logger.warning("invalid_rank_data", user_id=user_id, error=str(e))
            return None


# シングルトンインスタンス


_rank_service: RankService | None = None


def get_rank_service() -> RankService:
    """RankServiceのシングルトンインスタンスを取得"""
    global _rank_service
    if _rank_service is None:
        _rank_service = RankService()
    return _rank_service


