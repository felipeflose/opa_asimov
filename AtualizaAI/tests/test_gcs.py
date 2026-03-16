import unittest
from unittest.mock import MagicMock, patch
from src.storage.gcs_client import GCSClient
import json

class TestGCSClient(unittest.TestCase):
    @patch('google.cloud.storage.Client')
    def test_read_json_with_cache(self, mock_client):
        # Setup mock
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = '{"test": "data"}'
        
        client = GCSClient("test-bucket", project_id="test-proj")
        
        # First call (no cache)
        data1 = client.read_json("path.json")
        self.assertEqual(data1, {"test": "data"})
        self.assertEqual(mock_blob.download_as_text.call_count, 1)
        
        # Second call (should hit cache)
        data2 = client.read_json("path.json")
        self.assertEqual(data2, {"test": "data"})
        self.assertEqual(mock_blob.download_as_text.call_count, 1) # Should still be 1

if __name__ == '__main__':
    unittest.main()
