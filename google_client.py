from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from dto import GoogleFormResponse


class GoogleFormClient:
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.body.readonly",
        "https://www.googleapis.com/auth/forms.responses.readonly",
    ]
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    def __init__(self, form_id):
        self.form_id = form_id
        self.store = file.Storage("token.json")
        self.creds = self.store.get()
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets("client_secrets.json", self.SCOPES)
            self.creds = tools.run_flow(flow, self.store)

        self.form_service = discovery.build(
            "forms",
            "v1",
            http=self.creds.authorize(Http()),
            discoveryServiceUrl=self.DISCOVERY_DOC,
            static_discovery=False,
        )

    def get_form(self):
        form = self.form_service.forms().get(formId=self.form_id).execute()
        return form

    def get_responses(self) -> list[GoogleFormResponse]:
        responses = (
            self.form_service.forms().responses().list(formId=self.form_id).execute()
        )

        def extract_request(response) -> GoogleFormResponse:
            data = response["answers"]
            last_name = data["65f63cb0"]["textAnswers"]["answers"][0]["value"]
            first_name = data["22151de2"]["textAnswers"]["answers"][0]["value"]
            email = data["2c3e0b60"]["textAnswers"]["answers"][0]["value"]
            return GoogleFormResponse(
                first_name=first_name, last_name=last_name, email=email
            )

        return [extract_request(response) for response in responses["responses"]]


FORM_ID = "1rOeWWI7yNiFoG58D-DursJCdKSSERC8-Ntpw8pePVEc"  # 와플스튜디오 iOS 테스트플라이트 신청

if __name__ == "__main__":
    reader = GoogleFormClient(FORM_ID)
    responses = reader.get_responses()
    print(responses)
