"""Static, UI-only guidance for configuring supported AI providers."""

from __future__ import annotations

from html import escape
from typing import Final


PROVIDER_KEY_GUIDANCE: Final = {
    "groq": {
        "display_name": "Groq",
        "heading": "How to get your Groq API key",
        "api_keys_url": "https://console.groq.com/keys",
        "quickstart_url": "https://console.groq.com/docs/quickstart",
        "cta": "Open Groq API Keys",
        "steps": (
            "Sign in to GroqCloud.",
            "Select the project you want ApplyLens to use.",
            "Open API Keys and choose Create API Key.",
            "Copy the key and paste it here.",
        ),
        "provider_note": (
            "Groq API keys belong to the selected project. Groq restricts key "
            "management to permitted project/team roles."
        ),
    },
    "openai": {
        "display_name": "OpenAI",
        "heading": "How to get your OpenAI API key",
        "api_keys_url": "https://platform.openai.com/api-keys",
        "quickstart_url": "https://platform.openai.com/docs/quickstart/make-your-first-api-request",
        "cta": "Open OpenAI API Keys",
        "steps": (
            "Sign in to the OpenAI Platform.",
            "Open API Keys.",
            "Create an API key and copy it.",
            "Return here and paste the key into ApplyLens.",
        ),
        "provider_note": "",
    },
}

PROVIDER_KEY_SECURITY_NOTE: Final = (
    "Keep your key private. ApplyLens stores the saved credential encrypted and "
    "only displays a masked hint afterward."
)


def _external_link_icon_html() -> str:
    return (
        '<svg class="provider-key-guidance-external-icon" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true" focusable="false">'
        '<path d="M15 3h6v6"></path><path d="M10 14 21 3"></path>'
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>'
        "</svg>"
    )


def render_provider_key_guidance(provider: str) -> str:
    """Render one compact native disclosure from canonical static help content."""

    provider_name = str(provider or "").strip().lower()
    guidance = PROVIDER_KEY_GUIDANCE.get(provider_name)
    if guidance is None:
        return ""

    steps = "".join(f"<li>{escape(step)}</li>" for step in guidance["steps"])
    provider_note = (
        f'<p class="provider-key-guidance-note">{escape(guidance["provider_note"])}</p>'
        if guidance["provider_note"]
        else ""
    )
    external_icon = _external_link_icon_html()
    return f"""
      <details class="provider-key-guidance" data-provider-key-guidance="{escape(provider_name)}">
        <summary>
          <span>How to get your API key</span>
          <svg class="provider-key-guidance-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="m9 18 6-6-6-6"></path></svg>
        </summary>
        <div class="provider-key-guidance-content">
          <h4>{escape(guidance["heading"])}</h4>
          <ol>{steps}</ol>
          {provider_note}
          <div class="provider-key-guidance-links">
            <a href="{escape(guidance["api_keys_url"])}" target="_blank" rel="noopener noreferrer">{escape(guidance["cta"])}{external_icon}</a>
            <a href="{escape(guidance["quickstart_url"])}" target="_blank" rel="noopener noreferrer">Official quickstart{external_icon}</a>
          </div>
          <p class="provider-key-guidance-security">{escape(PROVIDER_KEY_SECURITY_NOTE)}</p>
        </div>
      </details>
""".strip()


def render_provider_key_guidance_templates() -> str:
    """Render reusable DOM templates for catalog-driven provider cards."""

    return "\n".join(
        f'<template id="providerKeyGuidanceTemplate-{escape(provider)}">'
        f"{render_provider_key_guidance(provider)}"
        "</template>"
        for provider in PROVIDER_KEY_GUIDANCE
    )
