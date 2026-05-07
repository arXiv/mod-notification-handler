from sqlalchemy import select, text
from arxiv.db.models import t_arXiv_moderators

def test_db_can_read(db_session):

    result = db_session.execute(select(t_arXiv_moderators))
    rows = result.mappings().all()

    assert len(rows) > 0
