from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.pi.services.functions import FunctionService
from app.modules.pi.services.groups import BeneficiaryAssignmentService, GroupService
from app.modules.pi.services.volunteers import VolunteerService


@pytest.fixture
def session() -> MagicMock:
    return MagicMock()


def build_service(service_cls, session: MagicMock, repo: MagicMock):
    service = service_cls.__new__(service_cls)
    service.repo = repo
    service.audit = MagicMock()
    repo.flush = session.flush
    repo.refresh = session.refresh
    repo.commit = session.commit
    repo.rollback = session.rollback
    return service


def actor():
    return SimpleNamespace(id=99, email="admin@example.com")


def test_function_create_trims_name_and_commits(session: MagicMock) -> None:
    repo = MagicMock()
    service = build_service(FunctionService, session, repo)
    function = SimpleNamespace(id=1, name="Koordynator")
    repo.get_by_name.return_value = None
    repo.create.return_value = function

    result = service.create_function(name="  Koordynator  ")

    assert result is function
    repo.get_by_name.assert_called_once_with("Koordynator")
    repo.create.assert_called_once_with(name="Koordynator")
    session.flush.assert_called_once()
    session.refresh.assert_called_once_with(function)
    session.commit.assert_called_once()


def test_function_create_rejects_blank_name_and_rolls_back(
    session: MagicMock,
) -> None:
    repo = MagicMock()
    service = build_service(FunctionService, session, repo)

    with pytest.raises(ValidationException):
        service.create_function(name="   ")

    repo.create.assert_not_called()
    session.rollback.assert_called_once()


def test_function_delete_rejects_system_function(session: MagicMock) -> None:
    repo = MagicMock()
    service = build_service(FunctionService, session, repo)
    repo.get_by_id.return_value = SimpleNamespace(id=1, is_system=True)

    with pytest.raises(ConflictError):
        service.delete_function(1)

    repo.delete.assert_not_called()
    session.rollback.assert_called_once()


def test_volunteer_create_rejects_duplicate_email(session: MagicMock) -> None:
    repo = MagicMock()
    service = build_service(VolunteerService, session, repo)
    repo.exists.return_value = True

    with pytest.raises(ConflictError):
        service.create_volunteer(actor=actor(), email="taken@example.com")

    repo.create.assert_not_called()
    session.rollback.assert_called_once()


def test_volunteer_create_syncs_functions_and_enriches(
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = MagicMock()
    service = build_service(VolunteerService, session, repo)
    volunteer = SimpleNamespace(
        id=5,
        full_name="Nowy Wolontariusz",
        email="new@example.com",
        phone=None,
        social_link=None,
        status="Aktywny",
        join_date=None,
        notes="",
        history="",
        function_ids=[1, 2],
    )
    repo.exists.return_value = False
    repo.create.return_value = volunteer
    sync_functions = MagicMock()
    monkeypatch.setattr(service, "_sync_functions", sync_functions)
    monkeypatch.setattr(service, "_enrich_volunteer", lambda item: item)

    result = service.create_volunteer(
        actor=actor(),
        full_name="Nowy Wolontariusz",
        email="new@example.com",
        function_ids=[1, 2],
    )

    assert result is volunteer
    repo.create.assert_called_once_with(
        full_name="Nowy Wolontariusz",
        email="new@example.com",
    )
    sync_functions.assert_called_once_with(5, [1, 2])
    session.commit.assert_called_once()


def test_beneficiary_get_by_id_raises_not_found(session: MagicMock) -> None:
    repo = MagicMock()
    service = build_service(BeneficiaryService, session, repo)
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_beneficiary_by_id(404)


def test_beneficiary_create_commits_and_enriches(
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = MagicMock()
    service = build_service(BeneficiaryService, session, repo)
    beneficiary = SimpleNamespace(
        id=1,
        full_name="Podopieczny",
        address="Adres",
        phone=None,
        family_phone=None,
        description="",
        group_id=None,
        status="OBECNY",
        bo_enrolled=False,
        last_priest_visit=None,
        last_volunteer_meeting=None,
        history="",
        group_name=None,
    )
    repo.create.return_value = beneficiary
    enrich = MagicMock(return_value=beneficiary)
    monkeypatch.setattr(service, "_enrich_beneficiary", enrich)

    result = service.create_beneficiary(
        actor=actor(), full_name="Podopieczny", address="Adres"
    )

    assert result is beneficiary
    repo.create.assert_called_once_with(full_name="Podopieczny", address="Adres")
    session.refresh.assert_called_once_with(beneficiary)
    session.commit.assert_called_once()
    enrich.assert_called_once_with(beneficiary)


def test_group_create_passes_assignments_to_replacement(
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = MagicMock()
    service = build_service(GroupService, session, repo)
    group = SimpleNamespace(id=3, name="Grupa")
    assignments = [{"beneficiary": 7, "volunteers": [{"id": 11}]}]
    repo.create.return_value = group
    repo.get_beneficiary.return_value = None
    replace_assignments = MagicMock()
    monkeypatch.setattr(service, "_replace_group_assignments", replace_assignments)
    monkeypatch.setattr(
        service,
        "get_group_detail",
        lambda group_id: {
            "id": group_id,
            "name": "Grupa",
            "leader_id": None,
            "beneficiaries": [],
        },
    )

    result = service.create_group(actor=actor(), name="Grupa", assignments=assignments)

    assert result == {
        "id": 3,
        "name": "Grupa",
        "leader_id": None,
        "beneficiaries": [],
    }
    repo.create.assert_called_once_with(name="Grupa")
    replace_assignments.assert_called_once_with(3, assignments)
    session.commit.assert_called_once()


def test_assignment_create_rejects_duplicate_pair(session: MagicMock) -> None:
    repo = MagicMock()
    service = build_service(BeneficiaryAssignmentService, session, repo)
    repo.get_by_beneficiary_volunteer.return_value = SimpleNamespace(id=1)

    with pytest.raises(ConflictError):
        service.create_assignment(beneficiary_id=1, volunteer_id=2, actor=actor())

    repo.create.assert_not_called()
    session.rollback.assert_called_once()


def test_assignment_create_commits_new_assignment(session: MagicMock) -> None:
    repo = MagicMock()
    service = build_service(BeneficiaryAssignmentService, session, repo)
    assignment = SimpleNamespace(
        id=1,
        beneficiary_id=1,
        volunteer_id=2,
        is_main=True,
        additional_info="",
    )
    repo.get_by_beneficiary_volunteer.return_value = None
    repo.create.return_value = assignment

    result = service.create_assignment(
        beneficiary_id=1,
        volunteer_id=2,
        actor=actor(),
        is_main=True,
    )

    assert result is assignment
    repo.create.assert_called_once_with(
        beneficiary_id=1,
        volunteer_id=2,
        is_main=True,
    )
    session.refresh.assert_called_once_with(assignment)
    session.commit.assert_called_once()
