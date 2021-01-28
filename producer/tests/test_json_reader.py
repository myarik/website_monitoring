import json
import re
from json.decoder import JSONDecodeError

import pytest

from producer.reader import JSONFileReader
from producer.schema import FILE_SCHEMA


def test_read_invalid_file_type(tmpdir):
    file_txt = tmpdir.join("text.txt")
    file_txt.write("content")
    with pytest.raises(JSONDecodeError):
        with JSONFileReader(file_txt, FILE_SCHEMA) as f:
            f.read()


def test_read_file_with_invalid_schema(tmpdir):
    file_invalid_json = tmpdir.join("example.json")
    data = {
        "name": "Foo Bar",
        "grades": [27, 38, 12],
    }
    with open(file_invalid_json, "w") as fh:
        json.dump(data, fh)

    with pytest.raises(TypeError):
        with JSONFileReader(file_invalid_json, FILE_SCHEMA) as f:
            f.read()


def test_read_file(tmpdir):
    json_file = tmpdir.join("example.json")
    data = [
        {
            "url": "https://www.example.org/",
            "regexp_pattern": "/^[a-z0-9_-]{3,16}$/",
        }
    ]
    with open(json_file, "w") as fh:
        json.dump(data, fh)

    with JSONFileReader(json_file, FILE_SCHEMA) as f:
        data = f.read()
    assert data == [
        {
            "url": "https://www.example.org/",
            "regexp_pattern": re.compile("/^[a-z0-9_-]{3,16}$/"),
        }
    ]
