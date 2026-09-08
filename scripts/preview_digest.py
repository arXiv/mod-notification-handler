"""write one moderator's digest to file, from the seeded test database, for eyeballing

    poetry run python -m scripts.preview_digest                     # every digest moderator
    poetry run python -m scripts.preview_digest digest-cat@example.com

Output goes to preview/<address>.txt and .html. Nothing is sent, no real database is touched:
this points arxiv.db at a throwaway copy of tests/data.sql, exactly as the test fixture does.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import arxiv.db as arxiv_db
from arxiv.db import Session
from arxiv.db.models import configure_db_engine

from tests.conftest import create_engine_for_db, get_seed_database

OUT_DIR = Path(__file__).resolve().parent.parent / "preview"


def _use_seeded_db(tmpdir: str) -> None:
    """point arxiv.db at a copy of the seeded test database"""
    tmp_db = Path(tmpdir) / "preview.sqlite.db"
    shutil.copyfile(get_seed_database(), tmp_db)
    configure_db_engine(create_engine_for_db(tmp_db), None)
    Session.remove()


def _write(address: str, digest) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for suffix, content in (("txt", digest.text), ("html", digest.html)):
        path = OUT_DIR / f"{address}.{suffix}"
        path.write_text(content, encoding="utf-8")
        print(f"  {path}")


def main(wanted: str = None) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        _use_seeded_db(tmpdir)

        #imported here so they bind to the seeded engine
        from app.daily_update.filters import get_subs_for_mod, report_on
        from app.daily_update.moderators import get_digest_recipients
        from app.daily_update.report_content import render_report
        from app.daily_update.submissions import get_open_submissions
        from app.shared.moderators import get_mod_emails

        recipients = get_digest_recipients()
        reportable = report_on(get_open_submissions())
        contacts = get_mod_emails(set(recipients))

        for mod in recipients.values():
            contact = contacts.get(mod.user_id)
            if contact is None or (wanted and contact.email != wanted):
                continue
            theirs = get_subs_for_mod(mod.categories, reportable)
            print(f"\n{contact.email} — {mod.header} — {len(theirs)} submissions")
            _write(contact.email, render_report(mod, theirs))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
