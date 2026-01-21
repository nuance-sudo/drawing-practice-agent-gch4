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

    def test_determine_rank(self):
        # 境界値テスト
        self.assertEqual(self.service.determine_rank(0), Rank.BRONZE)
        self.assertEqual(self.service.determine_rank(30), Rank.BRONZE)
        self.assertEqual(self.service.determine_rank(31), Rank.SILVER)
        self.assertEqual(self.service.determine_rank(50), Rank.SILVER)
        self.assertEqual(self.service.determine_rank(51), Rank.GOLD)
        self.assertEqual(self.service.determine_rank(70), Rank.GOLD)
        self.assertEqual(self.service.determine_rank(71), Rank.PLATINUM)
        self.assertEqual(self.service.determine_rank(85), Rank.PLATINUM)
        self.assertEqual(self.service.determine_rank(86), Rank.DIAMOND)
        self.assertEqual(self.service.determine_rank(100), Rank.DIAMOND)

        # 範囲外
        self.assertEqual(self.service.determine_rank(-1), Rank.BRONZE)
        self.assertEqual(self.service.determine_rank(101), Rank.DIAMOND)

    def test_update_user_rank_initial(self):
        """初回ランク更新"""
        user_id = "test_user"
        score = 60.0  # Gold
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
        self.assertEqual(result.current_rank, Rank.GOLD)
        self.assertEqual(result.current_score, score)

        # 呼び出し検証
        self.mock_collection.document.assert_called_with(user_id)
        mock_user_ref.set.assert_called_with({
            "rank": "Gold",
            "latest_score": score,
            "updated_at": unittest.mock.ANY,
        }, merge=True)

        # 履歴保存検証
        mock_user_ref.collection.assert_called_with("rank_history")
        mock_history_ref.set.assert_called()
        call_args = mock_history_ref.set.call_args[0][0]
        self.assertEqual(call_args["user_id"], user_id)
        self.assertEqual(call_args["old_rank"], None)
        self.assertEqual(call_args["new_rank"], "Gold")
        self.assertEqual(call_args["score"], score)
        self.assertEqual(call_args["task_id"], task_id)

    def test_update_user_rank_change(self):
        """ランク変更（昇格）"""
        user_id = "test_user"
        score = 90.0  # Diamond
        task_id = "test_task"

        # 既存ユーザー情報 (Gold)
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {"rank": "Gold", "latest_score": 60}
        mock_user_ref.get.return_value = mock_user_doc
        
        # rank_history コレクションモック
        mock_history_col = MagicMock()
        mock_history_ref = MagicMock()
        mock_user_ref.collection.return_value = mock_history_col
        mock_history_col.document.return_value = mock_history_ref

        self.mock_collection.document.return_value = mock_user_ref

        result = self.service.update_user_rank(user_id, score, task_id)

        # 結果検証
        self.assertEqual(result.current_rank, Rank.DIAMOND)
        
        # 履歴保存検証
        mock_history_ref.set.assert_called()
        call_args = mock_history_ref.set.call_args[0][0]
        self.assertEqual(call_args["old_rank"], "Gold")
        self.assertEqual(call_args["new_rank"], "Diamond")

    def test_update_user_rank_no_change(self):
        """ランク変更なし"""
        user_id = "test_user"
        score = 65.0  # Gold (変わらず)
        task_id = "test_task"

        # 既存ユーザー情報 (Gold)
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {"rank": "Gold", "latest_score": 60}
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_history_col = MagicMock()
        mock_user_ref.collection.return_value = mock_history_col

        self.mock_collection.document.return_value = mock_user_ref

        result = self.service.update_user_rank(user_id, score, task_id)

        # 結果検証
        self.assertEqual(result.current_rank, Rank.GOLD)
        
        # 変更がないので履歴は保存されないはず (初回でない)
        # ただし実装では rank_changed or is_first_time で判定してる
        # 今回は is_first_time=False, rank_changed=False なので保存されない
        mock_history_col.document.assert_not_called()
        
    def test_get_user_rank_exists(self):
        """ユーザーランク取得（存在する場合）"""
        user_id = "test_user"
        
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "rank": "Silver",
            "latest_score": 40.0,
            "updated_at": datetime.now()
        }
        mock_user_ref.get.return_value = mock_user_doc
        self.mock_collection.document.return_value = mock_user_ref
        
        result = self.service.get_user_rank(user_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.current_rank, Rank.SILVER)
        self.assertEqual(result.current_score, 40.0)

    def test_get_user_rank_not_found(self):
        """ユーザーランク取得（存在しない場合）"""
        user_id = "test_user"
        
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = False
        mock_user_ref.get.return_value = mock_user_doc
        self.mock_collection.document.return_value = mock_user_ref
        
        result = self.service.get_user_rank(user_id)
        
        self.assertIsNone(result)
