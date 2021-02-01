"""
Deserializer
"""
import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Optional, Any

import trafaret as t
from loguru import logger

from core.models import Response


REQUEST_SCHEMA = t.Dict(
    {
        t.Key("url"): t.URL,
        t.Key("load_time"): t.ToFloat,
        t.Key("request_time"): t.ToDateTime("%Y-%m-%dT%H:%M:%S.%f%z"),
        t.Key("status_code"): t.ToInt,
        t.Key("error"): t.String | t.Null,
    }
).ignore_extra("*")


@dataclass
class KafkaDeserializer:
    """
    Kafka deserializer
    """

    document_schema: t.Trafaret

    def __call__(
        self, serialized: bytes, *args: Any, **kwargs: Any
    ) -> Optional[Response]:
        try:
            raw_data = json.loads(serialized)
        except JSONDecodeError as error:
            logger.error(
                "receive invalid json object, error: {}".format(serialized, str(error))
            )
            return
        try:
            data = self.document_schema.check(raw_data)
        except t.DataError as err:
            logger.error("invalid document structure object, {}", err)
            return
        return Response(**data)
