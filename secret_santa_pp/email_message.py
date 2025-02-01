from datetime import date
from pathlib import Path

from pydantic import BaseModel


class TemplateManager(BaseModel):
    common_template_data: dict[str, str] = {}

    def __init__(
        self, event_name: str | None = None, event_date: date | None = None
    ) -> None:
        common_template_data = {
            "days_to_christmas": self._get_days_delta_text(
                self._get_christmas_date(), "Christmas"
            ),
            "year": f"{date.today().year}",
        }

        if event_name is not None:
            common_template_data["event_name"] = event_name

        if event_date is not None:
            common_template_data["event_date"] = event_date.strftime("%A, %d %B %Y")

        if event_name is not None and event_date is not None:
            common_template_data["days_to_event"] = self._get_days_delta_text(
                event_date, event_name
            )

        super().__init__(common_template_data=common_template_data)

    def _get_days_delta_text(self, event_date: date, event_name: str) -> str:
        days_delta = (event_date - date.today()).days
        return f"{days_delta} days to {event_name}"

    def _get_christmas_date(self) -> date:
        return date(self._get_current_year(), 12, 25)

    def _get_current_year(self) -> int:
        return date.today().year

    def populate(self, template_data: dict[str, str], text: str) -> str:
        combined_template_data = template_data | self.common_template_data
        return text.format(**combined_template_data)


class EmailMessage(BaseModel):
    subject: str
    message_html: str | None
    message_text: str | None
    template_manager: TemplateManager

    def __init__(
        self,
        template_manager: TemplateManager,
        subject: str,
        html_template: Path | None,
        text_template: Path | None,
    ) -> None:
        message_html = None
        if html_template is not None:
            with html_template.open() as fp:
                message_html = fp.read()

        message_text = None
        if text_template is not None:
            with text_template.open() as fp:
                message_text = fp.read()

        if message_html is None and message_text is None:
            msg = "Either HTML Template or Text Template must be specified"
            raise RuntimeError(msg)

        super().__init__(
            template_manager=template_manager,
            subject=subject,
            message_html=message_html,
            message_text=message_text,
        )

    def get_subject(self, template_data: dict[str, str]) -> str:
        return self.template_manager.populate(template_data, self.subject)

    def get_message_html(self, template_data: dict[str, str]) -> str | None:
        return (
            None
            if self.message_html is None
            else self.template_manager.populate(template_data, self.message_html)
        )

    def get_message_text(self, template_data: dict[str, str]) -> str | None:
        return (
            None
            if self.message_text is None
            else self.template_manager.populate(template_data, self.message_text)
        )
