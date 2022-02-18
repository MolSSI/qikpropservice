from typing import Optional, Tuple

from pydantic import BaseModel, Extra


class QikPropOptions(BaseModel):
    """Set of supported options in QikProp"""
    fast: bool = False
    similar: int = 20

    class Config:
        extra = Extra.allow


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


class SeverHelloGETResponse(BaseModel):
    title: str
    version: Tuple[int, int, int]

    @property
    def version_as_str(self):
        return ".".join(str(v) for v in self.version)


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


StatusCodes = _StatusCodes()
