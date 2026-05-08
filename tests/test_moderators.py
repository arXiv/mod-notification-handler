from sqlalchemy import select

from arxiv.db.models import t_arXiv_moderators

from app.moderators import get_all_moderators

def test_db_can_read(db_session):

    result = db_session.execute(select(t_arXiv_moderators))
    rows = result.mappings().all()

    assert len(rows) > 0

def test_get_mods(db_session):
    a, b = get_all_moderators()
    print(a)
    assert False

