"""DSMS apps models"""

import urllib.parse

from pydantic import BaseModel, Field

from dsms.core.utils import _perform_request


class App(BaseModel):
    """KItem app list"""

    filename: str = Field(
        ..., description="File name of the notebook in the DSMS."
    )
    basename: str = Field(
        ..., description="Base name of the notebook in the DSMS."
    )
    folder: str = Field(
        ..., description="Directory of the notebook in the DSMS."
    )

    def get(self, as_html: bool = False) -> str:
        """Download the jupyter notebook"""
        safe_filename = urllib.parse.quote_plus(self.filename)
        response = _perform_request(
            f"knowledge/api/apps/{safe_filename}",
            "get",
            params={"as_html": as_html},
        )
        if not response.ok:
            message = f"Something went wrong downloading app `{self.filename}`: {response.text}"
            raise RuntimeError(message)
        return response.text
