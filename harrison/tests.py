import json
from unittest.mock import MagicMock, patch

from django.test import TestCase


def case_study_slugs(case_studies):
    if isinstance(case_studies, dict):
        return list(case_studies)
    slugs = []
    for item in case_studies:
        if isinstance(item, dict):
            slugs.append(item["slug"])
        else:
            slugs.append(item.slug)
    return slugs


class CaseStudyDataTests(TestCase):
    def test_case_studies_slugs_in_order(self):
        from harrison.portfolio_data import CASE_STUDIES

        self.assertEqual(
            case_study_slugs(CASE_STUDIES),
            [
                "harrison-agent",
                "hostpro",
                "kena-coin",
                "ride-hailing",
                "domain-platform",
                "blockchain-app",
                "api-platform",
                "homeserver",
            ],
        )


class PublicPageContractTests(TestCase):
    def test_home_nav(self):
        response = self.client.get("/")
        self.assertContains(response, "Work")
        self.assertContains(response, "Lab")

    def test_work_index(self):
        response = self.client.get("/work/")
        self.assertContains(response, "Harrison Agent")
        self.assertContains(response, "HostPro")
        self.assertContains(response, "KENA Coin")
        self.assertContains(response, "Domain Management Platform")
        self.assertContains(response, "Blockchain Web Application")
        self.assertContains(response, "API Platform")
        self.assertContains(response, "Homeserver")

    def test_harrison_agent_detail(self):
        response = self.client.get("/work/harrison-agent/")
        self.assertContains(response, "Harrison Agent")
        self.assertContains(response, "http://197.248.201.233:2020/")
        self.assertContains(response, "Open the chat")

    def test_new_case_studies(self):
        for path in ("/work/hostpro/", "/work/kena-coin/", "/work/ride-hailing/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_domain_platform_detail(self):
        response = self.client.get("/work/domain-platform/")
        self.assertContains(response, "Domain Management Platform")
        self.assertContains(response, "The hard part")
        self.assertContains(response, "All work")

    def test_blockchain_app_detail(self):
        response = self.client.get("/work/blockchain-app/")
        self.assertEqual(response.status_code, 200)

    def test_api_platform_detail(self):
        response = self.client.get("/work/api-platform/")
        self.assertEqual(response.status_code, 200)

    def test_homeserver_detail(self):
        response = self.client.get("/work/homeserver/")
        self.assertEqual(response.status_code, 200)

    def test_unknown_case_study_is_404(self):
        response = self.client.get("/work/does-not-exist/")
        self.assertEqual(response.status_code, 404)

    def test_lab(self):
        response = self.client.get("/lab/")
        self.assertContains(response, 'id="lab-terminal"')
        self.assertContains(response, 'id="lab-input"')
        self.assertContains(response, "stk-demo")
        self.assertContains(response, "Simulated responses only")
        self.assertContains(response, "This diagram does not call a live API")
        self.assertContains(response, 'id="architecture"')
        self.assertContains(response, 'id="api-playground"')
        self.assertContains(response, 'id="flow-challenge"')

    def test_command_palette_is_on_home(self):
        response = self.client.get("/")
        self.assertContains(response, 'id="command-palette"')
        self.assertContains(response, 'id="terminal-dialog"')
        self.assertContains(response, "Explore projects")

    def test_about(self):
        response = self.client.get("/about/")
        self.assertContains(response, "Afripixel")
        self.assertContains(response, "Kaggle")
        self.assertContains(response, "Contact")
        self.assertNotContains(response, "University of Embu")
        self.assertNotContains(response, "BSc")
        self.assertNotContains(response, "Second Class")
        self.assertNotContains(response, "KCSE")
        self.assertNotContains(response, "Images are locked")
        self.assertNotContains(response, "Sign in to view")

    def test_home_and_chat_page_have_the_agent(self):
        home = self.client.get("/")
        chat = self.client.get("/chat/")
        self.assertContains(home, "Ask Harrison")
        self.assertContains(home, 'id="hm-fab"')
        self.assertContains(home, "agent-widget.js")
        self.assertContains(home, "AGENT_CHAT_URL")
        self.assertContains(chat, 'id="agent-form"')
        self.assertContains(chat, "Chat")

    def test_agent_rejects_a_blank_message(self):
        response = self.client.post(
            "/chat/send/",
            data=json.dumps({"message": "  "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_instant_faq_name(self):
        response = self.client.post(
            "/chat/send/",
            data=json.dumps({"message": "What is your full name?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["agent"], "instant")
        self.assertIn("Harrison", body["reply"])

    def test_agent_returns_the_bot_reply(self):
        payload = json.dumps({"reply": "HostPro uses Django, Docker, and Proxmox."}).encode()
        remote = MagicMock()
        remote.read.return_value = payload
        remote.__enter__.return_value = remote
        with patch("urllib.request.urlopen", return_value=remote) as opener:
            response = self.client.post(
                "/chat/send/",
                data=json.dumps({"message": "What stack powers HostPro?", "history": []}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "HostPro uses Django, Docker, and Proxmox.")
        from django.conf import settings
        self.assertEqual(opener.call_args[0][0].full_url, settings.AGENT_CHAT_URL)

    def test_login(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        response = self.client.get("/register/")
        self.assertEqual(response.status_code, 200)
