from django.conf import settings


def agent(request):
    return {
        "AGENT_CHAT_URL": getattr(
            settings,
            "AGENT_CHAT_URL",
            "https://supervisors-moral-dive-program.trycloudflare.com/chat",
        ),
    }
