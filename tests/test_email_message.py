from datetime import date, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from pytest_mock import MockerFixture

from secret_santa_pp.email_message import EmailMessage, TemplateManager

TODAY = date.today()
YEAR = date.today().year
DAYS_TO_CHRISTMAS = (date(YEAR, 12, 25) - TODAY).days


@pytest.mark.parametrize(
    ("event_name", "event_date", "expected_template_data"),
    [
        (
            None,
            None,
            {},
        ),
        (
            "name",
            None,
            {"event_name": "name"},
        ),
        (
            None,
            date(2024, 12, 15),
            {"event_date": "Sunday, 15 December 2024"},
        ),
        (
            "name",
            date(2024, 12, 15),
            {
                "event_name": "name",
                "event_date": "Sunday, 15 December 2024",
                "days_to_event": (f"{(date(2024, 12, 15) - TODAY).days} days to name"),
            },
        ),
    ],
)
def test_template_manager_init(
    event_name: str | None,
    event_date: date | None,
    expected_template_data: dict[str, str],
):
    common_expected_template_data = {
        "days_to_christmas": f"{DAYS_TO_CHRISTMAS} days to Christmas",
        "year": f"{YEAR}",
    }

    template_manager = TemplateManager(event_name, event_date)

    assert template_manager.common_template_data == (
        expected_template_data | common_expected_template_data
    )


@pytest.mark.parametrize(
    ("event_date", "event_name", "expected_text"),
    [
        (date.today() + timedelta(days=10), "name", "10 days to name"),
        (date.today() + timedelta(days=20), "name", "20 days to name"),
        (date.today() + timedelta(days=-10), "other name", "-10 days to other name"),
    ],
)
def test_template_manager_get_days_delta_text(
    event_date: date, event_name: str, expected_text: str
):
    template_manager = TemplateManager()
    text = template_manager.get_days_delta_text(event_date, event_name)
    assert text == expected_text


def test_template_manager_get_christmas_date():
    template_manager = TemplateManager()
    christmas_date = template_manager.get_christmas_date()
    assert christmas_date == date(YEAR, 12, 25)


def test_template_manager_get_current_year():
    template_manager = TemplateManager()
    year = template_manager.get_current_year()
    assert year == YEAR


@pytest.mark.parametrize(
    ("event_name", "event_date", "template_data", "text", "expected_text"),
    [
        (
            None,
            None,
            {},
            "{days_to_christmas} {year}",
            f"{DAYS_TO_CHRISTMAS} days to Christmas {YEAR}",
        ),
        (
            "name",
            date(2024, 12, 15),
            {},
            "{days_to_christmas} {year} {event_name} {event_date} {days_to_event}",
            (
                f"{DAYS_TO_CHRISTMAS} days to Christmas {YEAR} name Sunday, 15 December"
                f" 2024 {(date(2024, 12, 15) - TODAY).days} days to name"
            ),
        ),
        (
            "name",
            date(2024, 12, 15),
            {"tag1": 1, "tag2": 2},
            "{days_to_christmas} {year} {event_name} OTHER TEXT",
            f"{DAYS_TO_CHRISTMAS} days to Christmas {YEAR} name OTHER TEXT",
        ),
        (
            None,
            None,
            {"days_to_christmas": "500 days to Christmas", "tag1": 1, "tag2": 2},
            "{days_to_christmas} {tag2}",
            "500 days to Christmas 2",
        ),
    ],
)
def test_template_manager_populate(
    event_name: str,
    event_date: date,
    template_data: dict[str, str],
    text: str,
    expected_text: str,
):
    template_manager = TemplateManager(event_name, event_date)
    formatted_text = template_manager.populate(template_data, text)
    assert formatted_text == expected_text


def test_email_message_no_template_specified():
    msg = "Either HTML Template or Text Template must be specified"
    with pytest.raises(RuntimeError, match=msg):
        EmailMessage(TemplateManager(), "subject", None, None)


@pytest.mark.parametrize(
    ("subject", "html", "text"),
    [
        ("subject", "html template", None),
        ("email subject", None, "text template"),
        ("blank subject", "html template", "text template"),
    ],
)
def test_email_message_init(
    tmp_path: Path,
    subject: str,
    html: str | None,
    text: str | None,
):
    html_path = None
    if html is not None:
        html_path = tmp_path / "template.html"
        with html_path.open("w") as fp:
            fp.write(html)

    text_path = None
    if text is not None:
        text_path = tmp_path / "template.txt"
        with text_path.open("w") as fp:
            fp.write(text)

    template_manager = TemplateManager()
    message = EmailMessage(template_manager, subject, html_path, text_path)

    assert message.subject == subject
    assert message.message_html == html
    assert message.message_text == text
    assert message.template_manager == template_manager


def test_email_message_get_subject(tmp_path: Path, mocker: MockerFixture):
    mock_populate = mocker.patch(
        "secret_santa_pp.email_message.TemplateManager.populate", autospec=True
    )
    mock_populate.return_value = "populated email subject"

    html_path = tmp_path / "template.html"
    with html_path.open("w") as fp:
        fp.write("html template")

    template_manager = TemplateManager()
    template_data = {"tag1": "tag1data"}
    subject = "email subject"

    message = EmailMessage(template_manager, subject, html_path, None)

    assert message.get_subject(template_data) == "populated email subject"
    mock_populate.assert_called_once_with(template_manager, template_data, subject)


def test_email_message_get_message_html(tmp_path: Path, mocker: MockerFixture):
    mock_populate = mocker.patch(
        "secret_santa_pp.email_message.TemplateManager.populate", autospec=True
    )
    mock_populate.return_value = "populated message html"

    html_path = tmp_path / "template.html"
    with html_path.open("w") as fp:
        fp.write("html template")

    template_manager = TemplateManager()
    template_data = {"tag1": "tag1data"}

    message = EmailMessage(template_manager, "subject", html_path, None)

    assert message.get_message_html(template_data) == "populated message html"
    mock_populate.assert_called_once_with(
        template_manager, template_data, "html template"
    )


def test_email_message_get_message_html_is_none(tmp_path: Path, mocker: MockerFixture):
    mock_populate = mocker.patch(
        "secret_santa_pp.email_message.TemplateManager.populate", autospec=True
    )
    mock_populate.return_value = "populated message text"

    text_path = tmp_path / "template.txt"
    with text_path.open("w") as fp:
        fp.write("text template")

    template_manager = TemplateManager()
    template_data = {"tag1": "tag1data"}

    message = EmailMessage(template_manager, "subject", None, text_path)

    assert message.get_message_html(template_data) is None
    mock_populate.assert_not_called()


def test_email_message_get_message_text(tmp_path: Path, mocker: MockerFixture):
    mock_populate = mocker.patch(
        "secret_santa_pp.email_message.TemplateManager.populate", autospec=True
    )
    mock_populate.return_value = "populated message text"

    text_path = tmp_path / "template.txt"
    with text_path.open("w") as fp:
        fp.write("text template")

    template_manager = TemplateManager()
    template_data = {"tag1": "tag1data"}

    message = EmailMessage(template_manager, "subject", None, text_path)

    assert message.get_message_text(template_data) == "populated message text"
    mock_populate.assert_called_once_with(
        template_manager, template_data, "text template"
    )


def test_email_message_get_message_text_is_none(tmp_path: Path, mocker: MockerFixture):
    mock_populate = mocker.patch(
        "secret_santa_pp.email_message.TemplateManager.populate", autospec=True
    )
    mock_populate.return_value = "populated message html"

    html_path = tmp_path / "template.html"
    with html_path.open("w") as fp:
        fp.write("html template")

    template_manager = TemplateManager()
    template_data = {"tag1": "tag1data"}

    message = EmailMessage(template_manager, "subject", html_path, None)

    assert message.get_message_text(template_data) is None
    mock_populate.assert_not_called()
