from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Extra

from . import QikPropOptions
from .. import __version_spec__


class _StatusCodes(BaseModel):
    ready: int = 200
    created: int = 201  # used with post
    staged: int = 202
    error: int = 220
    unmatched: int = 409
    null: int = 404

    @property
    def values(self):
        return [v.default for v in self.__fields__.values()]


StatusCodes = _StatusCodes()  # Make the static status codes reference


class SeverHelloGETResponse(BaseModel):
    title: str = "QikProp v3 As A Service API"
    version: Tuple[int, int, int] = __version_spec__


class StatusGET(BaseModel):
    """Expected Model for GET method of status"""
    id: str

    class Config:
        extra = Extra.allow
        validate_assignment = True


class StatusGETReturn(StatusGET):
    code: int
    message: str
    error: Optional[str]


class ResultGET(StatusGET):
    """Expected model for GET method"""


class GETPOSTError(BaseModel):
    args: Dict[str, Any]
    error: str
    code: int = 400


class QikpropPOST(QikPropOptions):
    id: str


class QikpropPOSTResponse(QikpropPOST):
    code: int = StatusCodes.created

