# generated by datamodel-codegen:
#   filename:  https://opensource.ieee.org/2791-object/ieee-2791-schema/-/raw/master/provenance_domain.json
#   timestamp: 2022-09-13T23:51:55+00:00

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import (
    List,
    Optional,
)

from pydantic import (
    AnyUrl,
    BaseModel,
    EmailStr,
    Extra,
    Field,
)


class Status(Enum):
    unreviewed = "unreviewed"
    in_review = "in-review"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"


class Embargo(BaseModel):
    class Config:
        extra = Extra.forbid

    start_time: Optional[datetime] = Field(None, description="Beginning date of embargo period.")
    end_time: Optional[datetime] = Field(None, description="End date of embargo period.")


class ContributionEnum(Enum):
    authoredBy = "authoredBy"
    contributedBy = "contributedBy"
    createdAt = "createdAt"
    createdBy = "createdBy"
    createdWith = "createdWith"
    curatedBy = "curatedBy"
    derivedFrom = "derivedFrom"
    importedBy = "importedBy"
    importedFrom = "importedFrom"
    providedBy = "providedBy"
    retrievedBy = "retrievedBy"
    retrievedFrom = "retrievedFrom"
    sourceAccessedBy = "sourceAccessedBy"


class Contributor(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str = Field(..., description="Name of contributor", examples=["Charles Darwin"])
    affiliation: Optional[str] = Field(
        None, description="Organization the particular contributor is affiliated with", examples=["HMS Beagle"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="electronic means for identification and communication purposes",
        examples=["name@example.edu"],
    )
    contribution: List[ContributionEnum] = Field(
        ..., description="type of contribution determined according to PAV ontology"
    )
    orcid: Optional[AnyUrl] = Field(
        None,
        description="Field to record author information. ORCID identifiers allow for the author to curate their information after submission. ORCID identifiers must be valid and must have the prefix ‘https://orcid.org/’",
        examples=["http://orcid.org/0000-0002-1825-0097"],
    )


class ObjectId(BaseModel):
    __root__: str = Field(
        ...,
        description="A unique identifier that should be applied to each IEEE-2791 Object instance, generated and assigned by a IEEE-2791 database engine. IDs should never be reused",
    )


class Uri(BaseModel):
    class Config:
        extra = Extra.forbid

    filename: Optional[str] = None
    uri: AnyUrl
    access_time: Optional[datetime] = Field(
        None, description="Time stamp of when the request for this data was submitted"
    )
    sha1_checksum: Optional[str] = Field(
        None, description="output of hash function that produces a message digest", regex="[A-Za-z0-9]+"
    )


class ReviewItem(BaseModel):
    class Config:
        extra = Extra.forbid

    date: Optional[datetime] = None
    reviewer: Contributor = Field(..., description="Contributer that assigns IEEE-2791 review status.")
    reviewer_comment: Optional[str] = Field(
        None,
        description="Optional free text comment by reviewer",
        examples=["Approved by research institution staff. Waiting for approval from regulator"],
    )
    status: Status = Field(..., description="Current verification status of the IEEE-2791 Object")


class ProvenanceDomain(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str = Field(
        ...,
        description="Public searchable name for IEEE-2791 Object. This public field should take free text value using common biological research terminology supporting the terminology used in the usability_domain, external references (xref), and keywords sections.",
        examples=["HCV1a ledipasvir resistance SNP detection"],
    )
    version: str = Field(
        ...,
        description="Records the versioning of this IEEE-2791 Object instance. IEEE-2791 Object Version should adhere to semantic versioning as recommended by Semantic Versioning 2.0.0.",
        examples=["2.9"],
    )
    review: Optional[List[ReviewItem]] = Field(
        None,
        description="Description of the current verification status of an object in the review process. The unreviewed flag indicates that the object has been submitted, but no further evaluation or verification has occurred. The in-review flag indicates that verification is underway. The approved flag indicates that the IEEE-2791 Object has been verified and reviewed. The suspended flag indicates an object that was once valid is no longer considered valid. The rejected flag indicates that an error or inconsistency was detected in the IEEE-2791 Object, and it has been removed or rejected. The fields from the contributor object (described in section 2.1.10) is inherited to populate the reviewer section.",
    )
    derived_from: Optional[ObjectId] = Field(
        None,
        description="value of `ieee2791_id` field of another IEEE-2791 that this object is partially or fully derived from",
    )
    obsolete_after: Optional[datetime] = Field(
        None,
        description="If the object has an expiration date, this optional field will specify that using the ‘datetime’ type described in ISO-8601 format, as clarified by W3C https://www.w3.org/TR/NOTE-datetime.",
    )
    embargo: Optional[Embargo] = Field(
        None,
        description="If the object has a period of time during which it shall not be made public, that range can be specified using these optional fields. Using the datetime type, a start and end time are specified for the embargo.",
    )
    created: datetime = Field(..., description="Date and time of the IEEE-2791 Object creation")
    modified: datetime = Field(..., description="Date and time the IEEE-2791 Object was last modified")
    contributors: List[Contributor] = Field(
        ...,
        description="This is a list to hold contributor identifiers and a description of their type of contribution, including a field for ORCIDs to record author information, as they allow for the author to curate their information after submission. The contribution type is a choice taken from PAV ontology: provenance, authoring and versioning, which also maps to the PROV-O.",
    )
    license: str = Field(
        ...,
        description="Creative Commons license or other license information (text) space. The default or recommended license can be Attribution 4.0 International as shown in example",
        examples=["https://spdx.org/licenses/CC-BY-4.0.html"],
    )