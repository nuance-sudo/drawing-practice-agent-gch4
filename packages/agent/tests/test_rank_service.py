import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.models.rank import Rank, RankHistory, UserRank
from src.services.rank_service import RankService


class TestRankService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.collection.return_value = self.mock_collection
        self.service = RankService(db=self.mock_db)

    def test_calculate_rank(self):
        # 境界値テスト: 高スコア獲得数に基づくランク判定
        
        # 0回 -> 10級
        self.assertEqual(self.service.calculate_rank(0), Rank.KYU_10)
        
        # 1回 -> 9級
        self.assertEqual(self.service.calculate_rank(1), Rank.KYU_9)
        
        # 3回 -> 7級
        self.assertEqual(self.service.calculate_rank(3), Rank.KYU_7)
        
        # 10回 -> 1級
        self.assertEqual(self.service.calculate_rank(10), Rank.KYU_1)
        
        # 12回 -> 初段
        self.assertEqual(self.service.calculate_rank(12), Rank.DAN_1)
        
        # 30回 -> 師範
        self.assertEqual(self.service.calculate_rank(30), Rank.SHIHAN)
        
        # 100回 -> 師範 (上限)
        self.assertEqual(self.service.calculate_rank(100), Rank.SHIHAN)

    def test_update_user_rank_initial_high_score(self):
        """初回ランク更新 (80点以上) -> カウント1で9級へ"""
        user_id = "test_user"
        score = 85.0  # High score
        task_id = "test_task"

        # ユーザーが存在しない場合
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = False
        mock_user_ref.get.return_value = mock_user_doc
        
        # rank_history コレクションモック
        mock_history_col = MagicMock()
        mock_history_ref = MagicMock()
        mock_user_ref.collection.return_value = mock_history_col
        mock_history_col.document.return_value = mock_history_ref

        self.mock_collection.document.return_value = mock_user_ref

        result = self.service.update_user_rank(user_id, score, task_id)

        # 結果検証
        self.assertEqual(result.current_rank, Rank.KYU_9) # 1 high score -> 9級
        self.assertEqual(result.current_score, score)
        self.assertEqual(result.total_submissions, 1)
        self.assertEqual(len(result.high_scores), 1)

        # 呼び出し検証
        self.mock_collection.document.assert_called_with(user_id)
        mock_user_ref.set.assert_called_with({
            "rank": Rank.KYU_9.value,
            "latest_score": score,
            "total_submissions": 1,
            "high_scores": [score],
            "updated_at": unittest.mock.ANY,
        }, merge=True)

    def test_update_user_rank_increment(self):
        """既存ユーザーのランク更新"""
        user_id = "test_user"
        score = 90.0
        task_id = "test_task"

        # 既存ユーザー情報 (9級, 過去1回80点以上)
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "rank": Rank.KYU_9.value,
            "latest_score": 85.0,
            "total_submissions": 5,
            "high_scores": [85.0]
        }
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_history_col = MagicMock()
        mock_history_ref = MagicMock()
        mock_user_ref.collection.return_value = mock_history_col
        mock_history_col.document.return_value = mock_history_ref

        self.mock_collection.document.return_value = mock_user_ref

        # 今回も80点以上 -> high_scoresが2つになる -> 8級
        result = self.service.update_user_rank(user_id, score, task_id)

        # 結果検証
        self.assertEqual(result.current_rank, Rank.KYU_8) # 2 high scores -> 8級
        self.assertEqual(result.total_submissions, 6)
        self.assertEqual(len(result.high_scores), 2)
        
    def test_update_user_rank_no_high_score(self):
        """80点未満の場合、ランクは上がらないが提出回数は増える"""
        user_id = "test_user"
        score = 79.0 # Not a high score
        task_id = "test_task"

        # 既存ユーザー情報 (9級, 過去1回80点以上)
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "rank": Rank.KYU_9.value,
            "latest_score": 85.0,
            "total_submissions": 5,
            "high_scores": [85.0]
        }
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_history_col = MagicMock()
        mock_user_ref.collection.return_value = mock_history_col

        self.mock_collection.document.return_value = mock_user_ref

        # 今回79点 -> high_scoresの数は変わらず1 -> ランクは9級のまま
        result = self.service.update_user_rank(user_id, score, task_id)

        # 結果検証
        self.assertEqual(result.current_rank, Rank.KYU_9)
        self.assertEqual(result.total_submissions, 6)
        self.assertEqual(len(result.high_scores), 1)
        
        # ランクが変わっていないので履歴保存は呼ばれない (初回でもない)
        mock_history_col.document.assert_not_called()

    def test_get_user_rank_exists(self):
        """ユーザーランク取得（存在する場合）"""
        user_id = "test_user"
        
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "rank": Rank.KYU_5.value,
            "latest_score": 40.0,
            "total_submissions": 10,
            "high_scores": [80.0, 81.0, 82.0, 83.0, 84.0],
            "updated_at": datetime.now()
        }
        mock_user_ref.get.return_value = mock_user_doc
        self.mock_collection.document.return_value = mock_user_ref
        
        result = self.service.get_user_rank(user_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.current_rank, Rank.KYU_5)
        self.assertEqual(result.total_submissions, 10)
