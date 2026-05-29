"""Tests for `contract_review_repo`."""

import json

from app.repositories import contract_review_repo as repo
from app.schemas.commercial.review import ContractReviewResult, DeviationItem


class TestCreate:
    def test_create_minimal_in_progress(self, db, user_id):
        review = repo.create(db, user_id=user_id, review_type="vendor")
        assert review.id
        assert review.user_id == user_id
        assert review.review_type == "vendor"
        assert review.result_status == "in_progress"
        assert review.escalation_sent is False

    def test_create_with_metadata(self, db, user_id):
        review = repo.create(
            db,
            user_id=user_id,
            review_type="vendor",
            counterparty="供应商 A",
            agreement_name="MSA-2026",
            side="purchasing",
            annual_value=120000.50,
            file_name="msa.pdf",
        )
        assert review.counterparty == "供应商 A"
        assert review.annual_value == 120000.50

    def test_create_with_matter_id_string(self, db, user_id):
        # Phase A: matter_id is a plain nullable string, no FK validation.
        review = repo.create(
            db, user_id=user_id, review_type="vendor", matter_id="some-matter-uuid"
        )
        assert review.matter_id == "some-matter-uuid"


class TestGetAndList:
    def test_get_by_id_existing(self, db, user_id):
        created = repo.create(db, user_id=user_id, review_type="vendor")
        fetched = repo.get_by_id(db, created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_by_id_missing(self, db):
        assert repo.get_by_id(db, "00000000-0000-0000-0000-000000000000") is None

    def test_list_by_user_pagination(self, db, user_id):
        for i in range(5):
            repo.create(db, user_id=user_id, review_type="vendor", agreement_name=f"agr-{i}")
        items, total = repo.list_by_user(db, user_id=user_id, skip=0, limit=3)
        assert total == 5
        assert len(items) == 3

    def test_list_orders_by_created_at_desc(self, db, user_id):
        from datetime import datetime, timedelta

        a = repo.create(db, user_id=user_id, review_type="vendor", agreement_name="a")
        b = repo.create(db, user_id=user_id, review_type="vendor", agreement_name="b")
        c = repo.create(db, user_id=user_id, review_type="vendor", agreement_name="c")
        # Force distinct created_at so the primary sort key is unambiguous;
        # the secondary id-desc fallback only matters when ts are equal.
        base = datetime(2026, 5, 28, 12, 0, 0)
        a.created_at = base
        b.created_at = base + timedelta(seconds=1)
        c.created_at = base + timedelta(seconds=2)
        db.flush()

        items, _ = repo.list_by_user(db, user_id=user_id)
        ids_in_order = [r.id for r in items]
        # newest first => c, b, a
        assert ids_in_order == [c.id, b.id, a.id]

    def test_list_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-000000000002"
        db.add(User(id=other_id, email="other@test.local", hashed_password="x" * 60))
        db.flush()
        repo.create(db, user_id=user_id, review_type="vendor")
        repo.create(db, user_id=other_id, review_type="vendor")
        items, total = repo.list_by_user(db, user_id=user_id)
        assert total == 1
        assert items[0].user_id == user_id


class TestUpdateResult:
    def test_update_result_serializes_pydantic_result_json(self, db, user_id):
        review = repo.create(db, user_id=user_id, review_type="vendor")
        result = ContractReviewResult(
            summary="底线：3 处偏差，1 处必须红线上报。",
            deviations=[
                DeviationItem(
                    clause_key="liability_cap",
                    clause_label="责任上限",
                    playbook_position="100%",
                    contract_quote="50%",
                    why_it_matters="只能追回一半。",
                ),
            ],
            favorable_terms=["争议解决在我方所在地"],
            missing_terms=["数据保护条款"],
            required_approver="GC",
        )
        repo.update_result(
            db,
            review=review,
            result_status="yellow",
            result_summary=result.summary,
            result_memo="# Review memo\n...",
            result_json=result,
            required_approver="GC",
        )
        assert review.result_status == "yellow"
        decoded = json.loads(review.result_json)
        assert decoded["required_approver"] == "GC"
        assert decoded["deviations"][0]["clause_key"] == "liability_cap"

    def test_update_result_partial_does_not_clobber(self, db, user_id):
        review = repo.create(db, user_id=user_id, review_type="vendor")
        repo.update_result(db, review=review, result_status="green", result_summary="OK")
        repo.update_result(db, review=review, escalation_sent=True)
        assert review.result_status == "green"  # untouched
        assert review.result_summary == "OK"
        assert review.escalation_sent is True


class TestDelete:
    def test_delete(self, db, user_id):
        review = repo.create(db, user_id=user_id, review_type="vendor")
        repo.delete(db, review)
        assert repo.get_by_id(db, review.id) is None
