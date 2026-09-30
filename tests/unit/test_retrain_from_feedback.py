import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 registers all models
from backend.app.database.base import Base
from backend.app.models.feedback import Feedback
from backend.app.models.user import User
from scripts.retrain_from_feedback import curate_feedback_dataset, run_retraining


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(email="u@example.com", hashed_password="x", full_name="U")
    session.add(user)
    session.commit()
    yield session, user.id
    session.close()


def test_curate_dataset_accepts_valid_taxonomy_labels(db_session):
    session, user_id = db_session
    session.add(
        Feedback(user_id=user_id, feedback_type="category_correction", corrected_value="Food > Restaurants")
    )
    session.commit()

    df = curate_feedback_dataset(session)
    assert len(df) == 1
    assert df.iloc[0]["label"] == "Food > Restaurants"


def test_curate_dataset_rejects_invalid_category(db_session):
    session, user_id = db_session
    session.add(
        Feedback(user_id=user_id, feedback_type="category_correction", corrected_value="NotARealCategory > X")
    )
    session.commit()

    df = curate_feedback_dataset(session)
    assert len(df) == 0


def test_curate_dataset_ignores_other_feedback_types(db_session):
    session, user_id = db_session
    session.add(Feedback(user_id=user_id, feedback_type="prediction_correction", corrected_value="9000"))
    session.commit()

    df = curate_feedback_dataset(session)
    assert len(df) == 0


def test_curate_dataset_skips_malformed_corrected_value(db_session):
    session, user_id = db_session
    session.add(Feedback(user_id=user_id, feedback_type="category_correction", corrected_value="no-separator"))
    session.commit()

    df = curate_feedback_dataset(session)
    assert len(df) == 0


def test_run_retraining_produces_candidate_with_real_metrics(db_session):
    session, user_id = db_session
    session.add(
        Feedback(user_id=user_id, feedback_type="category_correction", corrected_value="Food > Restaurants")
    )
    session.commit()
    feedback_df = curate_feedback_dataset(session)

    metrics = run_retraining(feedback_df)
    assert metrics["feedback_rows_used"] == 1
    assert metrics["synthetic_rows_used"] > 0
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert metrics["candidate_version"]
    assert metrics["run_id"]
