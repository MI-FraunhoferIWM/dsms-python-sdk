"""App  property of a KItem"""

import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_serializer

from dsms.core.session import Session
from dsms.knowledge.utils import _perform_request, print_model


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

    # OVERRIDE
    def __str__(self):
        return print_model(self, "additional_properties")

    # OVERRIDE
    def __repr__(self) -> str:
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

    # OVERRIDE
    def __str__(self):
        return print_model(self, "job_status")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)


class App(BaseModel):
    """App of a KItem."""

    id: Optional[UUID] = Field(None, description="ID of the KItem")

    kitem_app_id: Optional[int] = Field(
        None, description="ID of the KItem App"
    )
    executable: str = Field(
        ...,
        description="Name of the executable related to the app",
        max_length=400,
    )
    title: str = Field(
        ..., description="Title of the appilcation", max_length=50
    )
    description: Optional[str] = Field(
        None,
        description="Description of the appilcation",
        max_length=1000,
    )
    tags: Optional[dict] = Field(
        None, description="Tags related to the appilcation"
    )
    additional_properties: Optional[AdditionalProperties] = Field(
        None, description="Additional properties related to the appilcation"
    )

    @model_serializer
    def serialize_app(self) -> Dict[str, Any]:
        """Serialize app model"""
        return {
            key: value
            for key, value in self.__dict__.items()
            if key not in ["id", "kitem_app_id"]
        }

    def run(
        self,
        wait=True,
        expose_sdk_config=False,
        **kwargs,
    ) -> None:
        """Run application.

        Args:
            wait (bool, optional): whether the job shall not be run asychronously
                (not in the background), but the object should wait until the job finished.
                Warning: this may lead to a request timeout for long running jobs!
                    Job details may not be associated anymore when this occurs.
            expose_sdk_config (bool, optional):
                Determines whether SDK parameters (such as host URL, SSL verification, etc.)
                should be passed through or propagated to the app using the SDK.
                If set to True, the SDK's configuration will be made available
                for the app to use, allowing it to inherit settings such as the host URL
                or SSL configuration. If False, the app will not have access to these parameters,
                and the SDK will handle its own configuration independently.
                Defaults to False.
            **kwargs (Any, optional): Additional arguments to be passed to the workflow.
                KItem ID is passed automatically

        """
        kwargs["kitem_id"] = str(self.id)
        if expose_sdk_config:
            kwargs[
                "access_token"
            ] = Session.dsms.config.token.get_secret_value()

        response = _perform_request(
            Session.dsms,
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
        if wait and Session.dsms.config.auto_refresh:
            item = Session.kitems.get(str(self.id))
            if item:
                item.refresh()
            else:
                warnings.warn(
                    f"Could not refresh KItem with ID {self.id} automatically."
                )

        return Job(name=submitted.get("name"), executable=self.executable)

    @property
    def inputs(self) -> Dict[str, Any]:
        """Inputs defined for the app from the webform builder"""
        route = f"api/knowledge/apps/argo/{self.executable}/inputs"
        response = _perform_request(Session.dsms, route, "get")
        if not response.ok:
            raise RuntimeError(
                f"Could not fetch app input schema: {response.text}"
            )
        return response.json()

    # OVERRIDE
    def __str__(self):
        return print_model(self, "app")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)


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

        response = _perform_request(Session.dsms, route, "get")
        if not response.ok:
            raise RuntimeError(f"Could not fetch job status: {response.text}")
        return JobStatus(**response.json())

    @property
    def artifacts(self) -> Dict[str, Any]:
        """Get the atrifcats of a finished job"""

        route = f"api/knowledge/apps/argo/job/{self.name}/artifacts"
        response = _perform_request(Session.dsms, route, "get")
        if not response.ok:
            raise RuntimeError(
                f"Could not fetch job artifacts: {response.text}"
            )
        return response.json()

    @property
    def logs(self) -> str:
        """Get the logs of a job"""
        route = f"api/knowledge/apps/argo/job/{self.name}/logs"
        response = _perform_request(Session.dsms, route, "get")
        if not response.ok:
            raise RuntimeError(f"Could not fetch job logs: {response.text}")
        return response.text

    # OVERRIDE
    def __str__(self):
        return print_model(self, "job")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)


class AppList(list):
    """KItemPropertyList for apps"""

    @property
    def by_title(self) -> Dict[str, App]:
        """Get apps by title"""
        return {app.title: app for app in self}

    @property
    def by_exe(self) -> Dict[str, App]:
        """Get apps by executable"""
        return {app.executable: app for app in self}
