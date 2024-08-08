"""App  property of a KItem"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_serializer

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import _perform_request

if TYPE_CHECKING:
    from typing import Callable


class AdditionalProperties(BaseModel):
    """Additional properties of"""

    triggerUponUpload: bool = Field(
        False,
        description="Whether the app should be triggered when a file is uploaded",
    )
    triggerUponUploadFileExtensions: Optional[List[str]] = Field(
        None,
        description="File extensions for which the upload shall be triggered.",
    )

    def __str__(self) -> str:
        """Pretty print the KItemPropertyList"""
        values = ", ".join(
            [f"{key}: {value}" for key, value in self.__dict__.items()]
        )
        return f"{{{values}}}"

    def __repr__(self) -> str:
        """Pretty print the Apps"""
        return str(self)


class JobStatus(BaseModel):
    """Status of a job"""

    phase: str = Field(..., description="General job app status")
    estimated_duration: Optional[Union[str, datetime]] = Field(
        None, description="Estimated duration of the job"
    )
    finished_at: Optional[Union[str, datetime]] = Field(
        None, description="Datetime when the job was finished"
    )
    started_at: Optional[Union[str, datetime]] = Field(
        None, description="Datetime when when the job was started"
    )
    message: Optional[str] = Field(
        None, description="General message of the job"
    )
    progress: Optional[str] = Field(
        None, description="Relative number of jobs which were finished"
    )


class App(KItemProperty):
    """App of a KItem."""

    kitem_app_id: Optional[int] = Field(
        None, description="ID of the KItem App"
    )
    executable: str = Field(
        ..., description="Name of the executable related to the app"
    )
    title: str = Field(..., description="Title of the appilcation")
    description: Optional[str] = Field(
        None, description="Description of the appilcation"
    )
    tags: Optional[dict] = Field(
        None, description="Tags related to the appilcation"
    )
    additional_properties: Optional[AdditionalProperties] = Field(
        None, description="Additional properties related to the appilcation"
    )

    # OVERRIDE
    @model_serializer
    def serialize_author(self) -> Dict[str, Any]:
        """Serialize author model"""
        return {
            key: value
            for key, value in self.__dict__.items()
            if key not in ["id", "kitem_app_id"]
        }

    def run(
        self,
        wait=True,
        set_token: bool = False,
        set_host_url: bool = False,
        **kwargs,
    ) -> None:
        """Run application.

        Args:
            wait (bool, optional): whether the job shall not be run asychronously
                (not in the background), but the object should wait until the job finished.
                Warning: this may lead to a request timeout for long running jobs!
                    Job details may not be associated anymore when this occurs.
            token (bool, optional): Whether the job also should receive the access
                 token as paramter.If `True`, the JWT will be set as parameter with
                 the name ´access_token`.
            **kwargs (Any, optional): Additional arguments to be passed to the workflow.
                KItem ID is passed automatically

        """
        kwargs["kitem_id"] = str(self.id)
        if set_token:
            kwargs[
                "access_token"
            ] = self.context.dsms.config.token.get_secret_value()
        if set_host_url:
            kwargs["host_url"] = str(self.context.dsms.config.host_url)

        response = _perform_request(
            f"api/knowledge/apps/argo/job/{self.executable}",
            "post",
            json=kwargs,
            params={"wait": wait},
        )
        if not response.ok:
            raise RuntimeError(
                f"Submission was not successful: {response.text}"
            )
        submitted = response.json()

        return Job(name=submitted.get("name"), executable=self.executable)

    @property
    def inputs(self) -> Dict[str, Any]:
        """Inputs defined for the app from the webform builder"""
        route = f"api/knowledge/apps/argo/{self.executable}/inputs"
        response = _perform_request(route, "get")
        if not response.ok:
            raise RuntimeError(
                f"Could not fetch app input schema: {response.text}"
            )
        return response.json()


class Job(BaseModel):
    """Job running an app"""

    name: str = Field(..., description="Name of the job submitted")

    executable: str = Field(
        ..., description="Name of the executable of the job"
    )

    @property
    def status(self) -> JobStatus:
        """Get the status of the currently running job"""

        route = f"api/knowledge/apps/argo/job/{self.name}/status"

        response = _perform_request(route, "get")
        if not response.ok:
            raise RuntimeError(f"Could not fetch job status: {response.text}")
        return JobStatus(**response.json())

    @property
    def artifacts(self) -> Dict[str, Any]:
        """Get the atrifcats of a finished job"""

        route = f"api/knowledge/apps/argo/job/{self.name}/artifacts"
        response = _perform_request(route, "get")
        if not response.ok:
            raise RuntimeError(
                f"Could not fetch job artifacts: {response.text}"
            )
        return response.json()

    @property
    def logs(self) -> str:
        """Get the logs of a job"""
        route = f"api/knowledge/apps/argo/job/{self.name}/logs"
        response = _perform_request(route, "get")
        if not response.ok:
            raise RuntimeError(f"Could not fetch job logs: {response.text}")
        return response.text


class AppsProperty(KItemPropertyList):
    """KItemPropertyList for apps"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        """App data model"""
        return App

    @property
    def k_property_helper(cls) -> None:
        """Not defined for Apps"""

    @property
    def by_title(cls) -> Dict[str, App]:
        """Get apps by title"""
        return {app.title: app for app in cls}

    @property
    def by_exe(cls) -> Dict[str, App]:
        """Get apps by executable"""
        return {app.executable: app for app in cls}
