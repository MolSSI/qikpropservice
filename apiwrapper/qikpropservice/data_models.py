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
    """
    Expected HTTP return codes that the QikProp Service API might return.

    Attributes
    ----------
    ready : 200 - GET and POST
        Task is ready to pull down.
    created: 201 - POST
        Submitted task has been accepted by the server and no issues on input validation.
    staged: 202 - GET
        Task is queued in the service but has not been processed or is in processing.
    error : 220 - GET
        Task has been processed but had an error associated with processing. See data dict or pull error file
        for details.
    null : 404 - GET
        No task exists on the server with a given ID
    unmatched : 409 - GET and POST
        For a provided task ID and file data, Checksum/hashing does not match
    """

    ready: int = 200
    created: int = 201
    staged: int = 202
    error: int = 220
    null: int = 404
    unmatched: int = 409

    @property
    def values(self):
        """List of all expected HTTP codes as ints."""
        return [v.default for v in self.__fields__.values()]


StatusCodes = _StatusCodes()  # Make this static
