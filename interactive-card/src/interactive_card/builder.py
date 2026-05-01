"""Card builder — construct interactive cards programmatically."""

from __future__ import annotations


class CardBuilder:
    """Fluent builder for interactive cards.

    Usage:
        card = (CardBuilder()
            .text("**Important**", bold=True)
            .text("Please review this request.")
            .fact_set({"Client": "John", "Amount": "$500"})
            .input("reply", "textarea", label="Your response")
            .input("priority", "select", label="Priority",
                   options={"low": "Low", "medium": "Medium", "high": "High"})
            .button("approve", "Approve", "primary", action_type="resolve")
            .button("send", "Send", "primary",
                    action_type="event", source="interactive:billing",
                    event_type="reply.sent", inputs="all", resolves=True)
            .button("dismiss", "Dismiss", "ghost", action_type="resolve")
            .build())
    """

    def __init__(self):
        self._body: list[dict] = []
        self._actions: list[dict] = []

    def text(self, content: str, bold: bool = False) -> CardBuilder:
        """Add a text element (supports markdown)."""
        el = {"type": "text", "text": content}
        if bold:
            el["weight"] = "bold"
        self._body.append(el)
        return self

    def fact_set(self, facts: dict[str, str]) -> CardBuilder:
        """Add a key-value grid."""
        self._body.append({
            "type": "fact-set",
            "facts": [{"label": k, "value": v} for k, v in facts.items()],
        })
        return self

    def media(self, url: str, mime: str, alt: str = "") -> CardBuilder:
        """Add a media element (image, video, file)."""
        self._body.append({"type": "media", "url": url, "mime": mime, "alt": alt})
        return self

    def input(
        self,
        id: str,
        input_type: str = "text",
        label: str = "",
        placeholder: str = "",
        options: dict[str, str] | None = None,
        value: str | int | bool = "",
    ) -> CardBuilder:
        """Add a form input.

        Args:
            id: Unique field identifier.
            input_type: text | textarea | select | toggle | date | number.
            label: Field label.
            placeholder: Placeholder text.
            options: For select — dict of value: label.
            value: Default value.
        """
        el: dict = {
            "type": "input",
            "id": id,
            "input_type": input_type,
        }
        if label:
            el["label"] = label
        if placeholder:
            el["placeholder"] = placeholder
        if value != "":
            el["value"] = value
        if options:
            el["options"] = [{"value": k, "label": v} for k, v in options.items()]
        self._body.append(el)
        return self

    def button(
        self,
        id: str,
        label: str,
        style: str = "primary",
        *,
        action_type: str = "resolve",
        url: str = "",
        method: str = "POST",
        source: str = "",
        event_type: str = "",
        related_to: str = "",
        payload: dict | None = None,
        inputs: str | list[str] = "none",
        resolves: bool = False,
    ) -> CardBuilder:
        """Add an action button.

        Args:
            id: Unique button identifier.
            label: Button text.
            style: primary | secondary | ghost | destructive.
            action_type: resolve | webhook | event | link.
            url: For webhook/link actions.
            method: HTTP method for webhook (default POST).
            source: Event source for event actions.
            event_type: Event type for event actions.
            related_to: Related event ID for event actions.
            payload: Extra payload for webhook/event actions.
            inputs: "all" | "none" | list of field IDs to include.
            resolves: Also resolve conversation after action.
        """
        action: dict = {"type": action_type}

        if action_type == "webhook":
            action["url"] = url
            action["method"] = method
            if payload:
                action["payload"] = payload
        elif action_type == "event":
            if source:
                action["source"] = source
            if event_type:
                action["event_type"] = event_type
            if related_to:
                action["related_to"] = related_to
            if payload:
                action["payload"] = payload
        elif action_type == "link":
            action["url"] = url

        btn: dict = {
            "id": id,
            "label": label,
            "style": style,
            "action": action,
        }
        if inputs != "none":
            btn["inputs"] = inputs
        if resolves:
            btn["resolves"] = True

        self._actions.append(btn)
        return self

    def build(self) -> dict:
        """Build the card dict."""
        return {
            "body": self._body,
            "actions": self._actions,
        }
