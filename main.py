import requests
from token_generator import get_jwt_token
from dto import *
from google_client import GoogleFormClient, FORM_ID
from datetime import datetime
import time
import re
from pydantic.error_wrappers import ValidationError


def rate_limit(func):
    def wrapper(*args, **kwargs):
        time.sleep(1)
        return func(*args, **kwargs)

    return wrapper


class AppStoreConnectClient:
    BASE_URL = "https://api.appstoreconnect.apple.com"

    def __init__(self) -> None:
        self.s = requests.Session()
        self.update_token()

    def update_token(self):
        token = get_jwt_token()
        self.s.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def _paginate(self, res_factory, res_url: str, *args):
        while True:
            res = self.s.get(res_url.format(*args))
            try:
                initial_response = res_factory(**res.json())
            except ValidationError as e:
                print(res.text)
                continue
            else:
                break
        while initial_response.links.next:
            res = self.s.get(initial_response.links.next)
            response = res_factory(**res.json())
            initial_response.data.extend(response.data)
            initial_response.links = response.links
        return initial_response

    @rate_limit
    def get_apps(self) -> AppsResponse:
        return self._paginate(AppsResponse, f"{self.BASE_URL}/v1/apps")

    @rate_limit
    def get_beta_groups(self, app: App) -> BetaGroupsResponse:
        return self._paginate(
            BetaGroupsResponse, f"{self.BASE_URL}/v1/apps/{app.id}/betaGroups"
        )

    @rate_limit
    def get_users(self) -> UsersResponse:
        return self._paginate(UsersResponse, f"{self.BASE_URL}/v1/users")

    @rate_limit
    def get_beta_testers(self):
        return self._paginate(BetaTestersResponse, f"{self.BASE_URL}/v1/betaTesters")

    @rate_limit
    def get_beta_testers_in_beta_group(
        self, beta_group: BetaGroup
    ) -> BetaTestersResponse:
        return self._paginate(
            BetaTestersResponse,
            f"{self.BASE_URL}/v1/betaGroups/{beta_group.id}/betaTesters",
        )

    @rate_limit
    def get_pending_invitations(self) -> UserInvitationsResponse:
        return self._paginate(
            UserInvitationsResponse,
            f"{self.BASE_URL}/v1/userInvitations",
        )

    @rate_limit
    def add_beta_group(self, app: App, payload: BetaGroupCreateRequest):
        res = self.s.post(
            f"{self.BASE_URL}/v1/apps/{app.id}/betaGroups",
            json=payload.dict(),
        )
        if res.status_code == 201:
            print(f"Successfully created beta group {payload.data.attributes.name}")
            return
        else:
            print(f"Failed to create beta group {payload.data.attributes.name}")
            print(res.json())
            return

    @rate_limit
    def add_beta_testers_to_group(
        self, beta_group: BetaGroup, payload: BetaTesterCreateRequest
    ):
        res = self.s.post(
            f"{self.BASE_URL}/v1/betaTesters",
            json=payload.dict(),
        )
        if res.status_code == 201:
            print(
                f"Successfully added {payload.data.attributes.email} to group {beta_group.attributes.name}"
            )
            return
        else:
            print(
                f"Failed to add {payload.data.attributes.email} to group {beta_group.attributes.name}"
            )
            print(res.json())
            return

    @rate_limit
    def patch_user(self, user: User, payload: dict):
        res = self.s.patch(
            f"{self.BASE_URL}/v1/users/{user.id}",
            json=payload,
        )
        if res.status_code == 200:
            print(
                f"Successfully changed roles for {user.attributes.username} to {payload}"
            )
            return
        else:
            print(f"Failed to change roles for {user.attributes.username}")
            print(res.text)

    @rate_limit
    def invite_user(self, invitation_request: UserInvitationCreateRequest):
        res = self.s.post(
            f"{self.BASE_URL}/v1/userInvitations",
            json=invitation_request.dict(),
        )
        if res.status_code == 201:
            print(f"Successfully invited {invitation_request.data.attributes.email}")
            return
        else:
            print(f"Failed to invite {invitation_request.data.attributes.email}")
            print(res.text)


class BusinessLogic:
    def __init__(self, bundle_ids: list[str]) -> None:
        self.bundle_ids = bundle_ids
        self.connect_client = AppStoreConnectClient()
        self.google_client = GoogleFormClient(form_id=FORM_ID)

    def find_all_users(self) -> list[User]:
        users = self.connect_client.get_users()
        return users.data

    def find_apps_by_bundle_ids(self, bundle_ids: list[str]) -> list[App]:
        apps = self.connect_client.get_apps()
        return [app for app in apps.data if app.attributes.bundleId in bundle_ids]

    def find_internal_beta_group(self, app: App) -> BetaGroup | None:
        beta_groups = self.connect_client.get_beta_groups(app)
        return next(
            (bg for bg in beta_groups.data if bg.attributes.isInternalGroup),
            None,
        )

    def create_internal_beta_group(self, app: App):
        self.connect_client.add_beta_group(
            app,
            BetaGroupCreateRequest(
                data=BetaGroupCreateRequest.Data(
                    attributes=BetaGroupCreateRequest.Data.Attributes(
                        name="Internal Testers",
                        isInternalGroup=True,
                        hasAccessToAllBuilds=True,
                        feedbackEnabled=True,
                    ),
                    relationships=BetaGroupCreateRequest.Data.Relationships(
                        app=BetaGroupCreateRequest.Data.Relationships.App(
                            data=BetaGroupCreateRequest.Data.Relationships.App.Data(
                                id=app.id, type="apps"
                            )
                        )
                    ),
                )
            ),
        )

    def resend_invitations_if_expired(self):
        pending_invitations = self.connect_client.get_pending_invitations()
        for invitation in pending_invitations.data:
            expiration_date = re.sub(r"\.\d+", "", invitation.attributes.expirationDate)
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S%z")
            if expiration_date < datetime.now(tz=expiration_date.tzinfo):
                self.connect_client.invite_user(
                    UserInvitationCreateRequest(
                        data=UserInvitationCreateRequest.Data(
                            attributes=UserInvitationCreateRequest.Data.Attributes(
                                email=invitation.attributes.email,
                                firstName=invitation.attributes.firstName,
                                lastName=invitation.attributes.lastName,
                                roles=invitation.attributes.roles,
                                allAppsVisible=invitation.attributes.allAppsVisible
                                or True,
                                provisioningAllowed=None,
                            ),
                        )
                    )
                )

    def find_user_by_email(self, email: str, users: list[User]) -> User | None:
        return next((user for user in users if user.attributes.username == email), None)

    def start_inviting(self):
        # Invite as internal users
        self.resend_invitations_if_expired()
        users = self.find_all_users()
        pending_invitations = self.connect_client.get_pending_invitations()
        user_emails = [user.attributes.username for user in users]
        user_emails_with_pending = user_emails + [
            invitation.attributes.email for invitation in pending_invitations.data
        ]
        responses = self.google_client.get_responses()
        for response in responses:
            if response.email in user_emails_with_pending:
                print(f"User {response.email} already exists or has pending invitation")
                continue
            self.connect_client.invite_user(
                UserInvitationCreateRequest(
                    data=UserInvitationCreateRequest.Data(
                        attributes=UserInvitationCreateRequest.Data.Attributes(
                            email=response.email,
                            firstName=response.first_name,
                            lastName=response.last_name,
                            roles=["SALES"],
                            allAppsVisible=True,
                            provisioningAllowed=None,
                        ),
                    )
                )
            )

        # Invite as beta testers for each app
        apps = self.find_apps_by_bundle_ids(bundle_ids=self.bundle_ids)
        for app in apps:
            internal_beta_group = self.find_internal_beta_group(app)
            if internal_beta_group is None:
                self.create_internal_beta_group(app)
                internal_beta_group = self.find_internal_beta_group(app)
            if internal_beta_group is None:
                print(f"Failed to create internal beta group for app {app}")
                return
            beta_testers = self.connect_client.get_beta_testers_in_beta_group(
                internal_beta_group
            )
            beta_tester_emails = [
                beta_tester.attributes.email for beta_tester in beta_testers.data
            ]
            for response in responses:
                if (
                    user := self.find_user_by_email(response.email, users)
                ) is None or response.email in beta_tester_emails:
                    print(f"Skip {response.email} for app {app.attributes.bundleId}")
                    continue

                self.connect_client.add_beta_testers_to_group(
                    internal_beta_group,
                    payload=BetaTesterCreateRequest(
                        data=BetaTesterCreateRequest.Data(
                            attributes=BetaTesterCreateRequest.Data.Attributes(
                                email=user.attributes.username,
                                firstName=user.attributes.firstName,
                                lastName=user.attributes.lastName,
                            ),
                            relationships=BetaTesterCreateRequest.Data.Relationships(
                                betaGroups=BetaTesterCreateRequest.Data.Relationships.BetaGroups(
                                    data=[
                                        BetaTesterCreateRequest.Data.Relationships.BetaGroups.Data(
                                            id=internal_beta_group.id, type="betaGroups"
                                        )
                                    ]
                                )
                            ),
                        ),
                    ),
                )

    def start_loop(self):
        while True:
            print(f"Starting Loop at {datetime.now()}")
            try:
                self.connect_client.update_token()
                self.start_inviting()
            except Exception as e:
                print(e)
            else:
                continue


if __name__ == "__main__":
    bl = BusinessLogic(
        bundle_ids=[
            "com.wafflestudio.toyproject2022.team2",
            "com.wafflestudio.toyproject2022.team5",
        ]
    )
    bl.start_loop()
