from pydantic import BaseModel, Extra


class QikPropOptions(BaseModel):
    """Set of supported options in QikProp"""
    fast: bool = False
    similar: int = 20

    class Config:
        extra = Extra.allow
