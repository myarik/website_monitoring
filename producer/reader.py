"""
This module represents a source readers
"""
import json
from typing import List, Dict, Any, ClassVar
import trafaret as t

from loguru import logger


class JSONFileReader:
    """
    JSON input data reader

    Attributes:
       file_name: A path to a filename
       validator: A validator based on a trafaret class
    """

    def __init__(self, file_name: str, validator: ClassVar) -> None:
        self.file_name = file_name
        self.validator = validator

    def __enter__(self):
        self.file_obj = open(  # pylint: disable=attribute-defined-outside-init
            self.file_name
        )
        return self

    def read(self) -> List[Dict[str, Any]]:
        """
        reads and validates an input data
        """
        raw_data = json.load(self.file_obj)
        try:
            return self.validator.check(raw_data)
        except t.DataError as err:
            logger.error("invalid file structure, {}", err.as_dict())
            raise TypeError("invalid file structure") from t.DataError

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file_obj.close()
        if exc_type is not None:
            if exc_type == json.decoder.JSONDecodeError:
                logger.error("invalid source file")
            return False
        return True
