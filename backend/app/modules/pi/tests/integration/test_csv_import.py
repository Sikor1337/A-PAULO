"""Integration tests for CSV bulk import (PAP-81)."""

import io


def _upload(api_client, url: str, csv_text: str, encoding: str = "utf-8-sig"):
    content = io.BytesIO(csv_text.encode(encoding))
    return api_client.post(url, files={"file": ("import.csv", content, "text/csv")})


def test_volunteer_template_download(api_client) -> None:
    response = api_client.get("/api/v1/imports/volunteers/template")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "formatka-wolontariusze.csv" in response.headers["content-disposition"]
    assert "Imię i nazwisko;Email" in response.content.decode("utf-8-sig")


def test_beneficiary_template_download(api_client) -> None:
    response = api_client.get("/api/v1/imports/beneficiaries/template")
    assert response.status_code == 200
    assert "formatka-podopieczni.csv" in response.headers["content-disposition"]
    assert "Imię i nazwisko;Adres" in response.content.decode("utf-8-sig")


def test_import_volunteers_happy_path(api_client) -> None:
    csv_text = (
        "Imię i nazwisko;Email;Telefon;Link społecznościowy;Status;"
        "Data przystąpienia;Notatki\r\n"
        "Anna Nowak;anna.nowak@example.com;+48 123 456 789;;Aktywny;"
        "2026-01-15;Notatka\r\n"
        "Jan Kowalski;jan.kowalski@example.com;;;Były;15.02.2026;\r\n"
    )
    response = _upload(api_client, "/api/v1/imports/volunteers", csv_text)
    assert response.status_code == 200
    report = response.json()
    assert report["ok"] is True
    assert report["total_rows"] == 2
    assert report["imported"] == 2
    assert report["errors"] == []
    assert report["skipped"] == []

    listing = api_client.get("/api/v1/volunteers").json()
    emails = {volunteer["email"] for volunteer in listing}
    assert {"anna.nowak@example.com", "jan.kowalski@example.com"} <= emails
    jan = next(v for v in listing if v["email"] == "jan.kowalski@example.com")
    assert jan["status"] == "Były"
    assert jan["join_date"].startswith("2026-02-15")


def test_import_volunteers_comma_delimiter(api_client) -> None:
    csv_text = "Imię i nazwisko,Email\r\nOla Przecinek,ola.przecinek@example.com\r\n"
    response = _upload(api_client, "/api/v1/imports/volunteers", csv_text)
    assert response.status_code == 200
    assert response.json()["imported"] == 1


def test_import_volunteers_validation_blocks_whole_file(api_client) -> None:
    csv_text = (
        "Imię i nazwisko;Email;Status\r\n"
        "Dobra Osoba;dobra@example.com;Aktywny\r\n"
        ";zly-email;Nieistniejący\r\n"
    )
    response = _upload(api_client, "/api/v1/imports/volunteers", csv_text)
    assert response.status_code == 200
    report = response.json()
    assert report["ok"] is False
    assert report["imported"] == 0
    messages = " | ".join(issue["message"] for issue in report["errors"])
    assert "wymagane" in messages
    assert "email" in messages.lower()
    assert all(issue["row"] == 3 for issue in report["errors"])

    listing = api_client.get("/api/v1/volunteers").json()
    assert all(v["email"] != "dobra@example.com" for v in listing)


def test_import_volunteers_skips_duplicates(api_client) -> None:
    created = api_client.post(
        "/api/v1/volunteers",
        json={
            "full_name": "Istniejąca Osoba",
            "email": "istnieje@example.com",
            "join_date": "2026-01-01T00:00:00",
        },
    )
    assert created.status_code == 200

    csv_text = (
        "Imię i nazwisko;Email\r\n"
        "Istniejąca Osoba;ISTNIEJE@example.com\r\n"
        "Nowa Osoba;nowa@example.com\r\n"
        "Nowa Osoba Bis;nowa@example.com\r\n"
    )
    response = _upload(api_client, "/api/v1/imports/volunteers", csv_text)
    report = response.json()
    assert report["ok"] is True
    assert report["imported"] == 1
    assert len(report["skipped"]) == 2
    assert report["skipped"][0]["row"] == 2
    assert report["skipped"][1]["row"] == 4


def test_import_volunteers_rejects_unknown_columns(api_client) -> None:
    response = _upload(
        api_client,
        "/api/v1/imports/volunteers",
        "Imię i nazwisko;Email;Kolor oczu\r\nOsoba;osoba@example.com;zielone\r\n",
    )
    assert response.status_code == 422
    assert "Kolor oczu" in response.json()["detail"]


def test_import_volunteers_cp1250_fallback(api_client) -> None:
    csv_text = "Imię i nazwisko;Email\r\nStanisław Żółć;zolc@example.com\r\n"
    response = _upload(
        api_client, "/api/v1/imports/volunteers", csv_text, encoding="cp1250"
    )
    report = response.json()
    assert report["ok"] is True
    assert report["imported"] == 1
    listing = api_client.get("/api/v1/volunteers").json()
    assert any(v["full_name"] == "Stanisław Żółć" for v in listing)


def test_import_beneficiaries_happy_path_and_duplicates(api_client) -> None:
    csv_text = (
        "Imię i nazwisko;Adres;Telefon;Telefon rodziny;Status;BO;"
        "Ostatnia wizyta księdza;Ostatnie spotkanie wolontariusza;Opis\r\n"
        "Maria Podopieczna;ul. Testowa 1;;;OBECNY;TAK;2026-05-01;;Opis osoby\r\n"
        "maria podopieczna;ul. Inna 2;;;OBECNY;NIE;;;\r\n"
    )
    response = _upload(api_client, "/api/v1/imports/beneficiaries", csv_text)
    report = response.json()
    assert report["ok"] is True
    assert report["imported"] == 1
    assert len(report["skipped"]) == 1
    assert report["skipped"][0]["row"] == 3

    listing = api_client.get("/api/v1/beneficiaries").json()
    maria = next(b for b in listing if b["full_name"] == "Maria Podopieczna")
    assert maria["bo_enrolled"] is True
    assert maria["last_priest_visit"] == "2026-05-01"


def test_import_beneficiaries_invalid_flag_and_status(api_client) -> None:
    csv_text = (
        "Imię i nazwisko;Adres;Status;BO\r\n"
        "Osoba Testowa;ul. Krótka 3;NIEZNANY;MOŻE\r\n"
    )
    response = _upload(api_client, "/api/v1/imports/beneficiaries", csv_text)
    report = response.json()
    assert report["ok"] is False
    assert report["imported"] == 0
    assert len(report["errors"]) == 2


def test_import_rejects_empty_file(api_client) -> None:
    response = _upload(api_client, "/api/v1/imports/volunteers", "")
    assert response.status_code == 422
