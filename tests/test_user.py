import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from app.db.models import User, Admin, UserStatus
from app.db import get_db
from app.utils.jwt import create_admin_token
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

class TestUserRouter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = next(get_db())

        self.admin = Admin(
            username="test_admin",
            hashed_password="password",
            two_factor_enabled=False
        )
        self.db.add(self.admin)
        self.db.commit()

        self.token = create_admin_token(
            username=self.admin.username,
            is_sudo=self.admin.is_sudo
        )

        self.expired_user = User(
            username="expired_user",
            expire=(datetime.now(timezone.utc) - timedelta(days=1)).timestamp(),
            status=UserStatus.expired,
            admin_id=self.admin.id
        )
        self.db.add(self.expired_user)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.delete(self.admin)
        self.db.commit()

    @patch('app.xray.operations.remove_user')
    def test_delete_expired_users_removes_user_from_xray(self, mock_remove_user):
        # Call the delete_expired_users endpoint
        response = self.client.delete(
            f"/api/users/expired?expired_before={quote_plus(datetime.now(timezone.utc).isoformat())}",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        # Check that the user was removed from the database
        self.assertEqual(response.status_code, 200)
        self.assertIn("expired_user", response.json())

        # Check that xray.operations.remove_user was called
        mock_remove_user.assert_called_once()

        # Cleanup
        self.db.expunge(self.expired_user)
        self.db.commit()

if __name__ == '__main__':
    unittest.main()
