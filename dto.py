from pydantic import BaseModel


class GoogleFormResponse(BaseModel):
    last_name: str
    first_name: str
    email: str


class ResourceLinks(BaseModel):
    self: str


class PagingInformation(BaseModel):
    class Paging(BaseModel):
        total: int
        limit: int

    paging: Paging


class PagedDocumentLinks(BaseModel):
    self: str
    first: str | None
    next: str | None


class User(BaseModel):
    class Attributes(BaseModel):
        username: str
        firstName: str
        lastName: str
        roles: list
        allAppsVisible: bool
        provisioningAllowed: bool

    class Relationships(BaseModel):
        visibleApps: dict

    id: str
    type: str
    attributes: Attributes
    relationships: Relationships | None
    links: ResourceLinks


class UsersResponse(BaseModel):
    data: list[User]
    links: PagedDocumentLinks
    meta: PagingInformation


class UserInvitationCreateRequest(BaseModel):
    class Data(BaseModel):
        class Attributes(BaseModel):
            email: str
            firstName: str
            lastName: str
            roles: list[str]
            allAppsVisible: bool
            provisioningAllowed: bool | None

        attributes: Attributes
        type: str = "userInvitations"

    data: Data


class App(BaseModel):
    class Attributes(BaseModel):
        bundleId: str
        name: str
        sku: str

    class Relationships(BaseModel):
        class BetaGroups(BaseModel):
            class Data(BaseModel):
                id: str
                type: str = "betaGroups"

            class Links(BaseModel):
                self: str
                related: str

            data: list[Data] | None
            links: Links
            meta: PagingInformation | None

        betaGroups: BetaGroups

    id: str
    type: str
    attributes: Attributes
    relationships: Relationships | None
    links: ResourceLinks


class AppsResponse(BaseModel):
    data: list[App]
    links: PagedDocumentLinks


class BetaGroup(BaseModel):
    class Attributes(BaseModel):
        name: str
        isInternalGroup: bool | None
        hasAccessToAllBuilds: bool | None

    attributes: Attributes
    id: str
    type: str
    links: ResourceLinks


class BetaTestersResponse(BaseModel):
    class BetaTester(BaseModel):
        class Attributes(BaseModel):
            firstName: str
            lastName: str | None
            email: str | None
            inviteType: str

        attributes: Attributes
        id: str
        type: str
        links: ResourceLinks

    data: list[BetaTester]
    links: PagedDocumentLinks
    meta: PagingInformation


class BetaGroupsResponse(BaseModel):
    data: list[BetaGroup]
    links: PagedDocumentLinks
    meta: PagingInformation


class BetaGroupCreateRequest(BaseModel):
    class Data(BaseModel):
        class Attributes(BaseModel):
            name: str
            isInternalGroup: bool
            hasAccessToAllBuilds: bool | None
            feedbackEnabled: bool | None

        class Relationships(BaseModel):
            class App(BaseModel):
                class Data(BaseModel):
                    id: str
                    type: str = "apps"

                data: Data

            app: App

        attributes: Attributes
        relationships: Relationships
        type: str = "betaGroups"

    data: Data


class BetaGroupBetaTestersLinkagesRequest(BaseModel):
    class Data(BaseModel):
        id: str
        type: str = "betaTesters"

    data: list[Data]


class UserInvitationsResponse(BaseModel):
    class UserInvitation(BaseModel):
        class Attributes(BaseModel):
            email: str
            firstName: str
            lastName: str
            roles: list[str]
            allAppsVisible: bool | None
            provisioningAllowed: bool | None
            expirationDate: str

        class Relationships(BaseModel):
            class VisibleApps(BaseModel):
                class Data(BaseModel):
                    id: str
                    type: str = "apps"

                data: list[Data] | None

            visibleApps: VisibleApps

        attributes: Attributes
        id: str
        type: str
        relationships: Relationships | None
        links: ResourceLinks

    data: list[UserInvitation]
    links: PagedDocumentLinks
    meta: PagingInformation


class BetaTesterCreateRequest(BaseModel):
    class Data(BaseModel):
        class Attributes(BaseModel):
            firstName: str
            lastName: str
            email: str

        class Relationships(BaseModel):
            class BetaGroups(BaseModel):
                class Data(BaseModel):
                    id: str
                    type: str = "betaGroups"

                data: list[Data]

            betaGroups: BetaGroups

        attributes: Attributes
        relationships: Relationships
        type: str = "betaTesters"

    data: Data
