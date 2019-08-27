import os
import json


def get_mock_data(mock_data_path):
    with open(mock_data_path, 'r') as f:
        data = json.loads(f.read())

    return data


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MOCKED_DATA_PATH = os.path.join(TEST_DIR, 'mocked_data')
