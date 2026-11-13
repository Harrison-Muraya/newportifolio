from django.conf import settings


def agent(request):
    return {
        "AGENT_CHAT_URL": getattr(
            settings,
            "AGENT_CHAT_URL",
            "http://197.248.201.233:2020/chat",
        ),
    }
