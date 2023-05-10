import unittest
from unittest.mock import patch
from main import app, redis_client
import os
import redis

from dotenv import load_dotenv
import main

load_dotenv()


class TestMain(unittest.TestCase):
    @patch("redis.Redis.from_url")
    def test_redis_connection(self, mock_redis):
        with patch.dict("os.environ", {"REDIS_HOST": "localhost", "REDIS_PORT": "6379", "REDIS_DB": "1"}):
            redis_mock = mock_redis.return_value
            redis_mock.ping.return_value = True
            redis_mock.get.return_value = b"0"
            main.redis_client = redis_mock
            assert main.redis_client.ping()

    def test_get_all_tools(self):
        with app.test_client() as c:
            response = c.get("/tools")
            assert response.status_code == 200
            assert response.content_type == "application/json"

    # def test_request_count(self):
    #     print(os.environ.get("REDIS_HOST"))
    #     print(os.environ.get("REDIS_PORT"))
    #     print(os.environ.get("REDIS_DB"))

    #     redis_client.delete('tool_requests')
    #     with app.test_client() as c:
    #         response = c.get("/tools")
    #         assert redis_client.get("tool_requests") == b"0"

    #         response = c.get("/tools")
    #         assert redis_client.get("tool_requests") == b"2"

    #         response = c.get("/tools")
    #         assert redis_client.get("tool_requests") == b"3"

    #         response = c.get("/tools")
    #         assert redis_client.get("tool_requests") == b"4"

    #         response = c.get("/tools")
    #         assert redis_client.exists("tools")
