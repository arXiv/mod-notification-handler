"""arranges one moderator's submissions into report sections and renders them"""
from enum import IntEnum, auto

from arxiv.submission import statuses

from app.daily_update.submissions import OpenSubmission
from app.daily_update.filters import proposal_cats
from app.daily_update.moderators import DigestMod
from app.daily_update.templates.entry import render_entry
from app.daily_update.templates.report_body import Section, render_body
from app.shared.templates import Rendered


def section_for(sub: OpenSubmission) -> Section:
    """which part of the report this submission appears under. on hold beats type"""
    if sub.status == statuses.ON_HOLD:
        return Section.HOLD
    if sub.sub_type == "new":
        return Section.NEW
    if sub.sub_type == "cross":
        return Section.CROSS
    #should not be reachable
    raise ValueError(f"submission {sub.submission_id}: no section for type {sub.sub_type}")


class MatchRank(IntEnum):
    """how a submission sorts within its section, by how the moderator's category appears on
    it. listed best first, and compares as a number so it can be a sort key"""
    PRIMARY = auto()
    PROPOSED = auto()
    SECONDARY = auto()


def match_rank(sub: OpenSubmission, categories: set[str]) -> MatchRank:
    """primary first, then proposed, then secondary"""
    if sub.primary_category in categories:
        return MatchRank.PRIMARY
    if proposal_cats(sub) & categories:
        return MatchRank.PROPOSED
    if set(sub.secondary_categories) & categories:
        return MatchRank.SECONDARY
    #get_subs_for_mod only hands over submissions that matched somewhere, so nothing gets here
    raise ValueError(
        f"submission {sub.submission_id}: nothing matches {sorted(categories)}"
    )


def bucket(
    submissions: list[OpenSubmission], categories: set[str]
) -> dict[Section, list[OpenSubmission]]:
    """group one digest's submissions into its sections and sort each one
    sorted by matching the primary category, a proposed category then a secondary category
    Submissions arrive newest first and the sort is stable, so submit time breaks ties."""
    
    buckets: dict[Section, list[OpenSubmission]] = {section: [] for section in Section}
    #break into sections
    for sub in submissions:
        buckets[section_for(sub)].append(sub)

    # sort within buckets
    for subs in buckets.values():
        subs.sort(key=lambda s: match_rank(s, categories))

    return buckets



def render_entries(
    buckets: dict[Section, list[OpenSubmission]],
) -> dict[Section, list[Rendered]]:
    """swap each submission for its rendered (text, html) pair, keeping the grouping

    In:  {Section.NEW: [submission, submission], ...}
    Out: {Section.NEW: [Rendered, Rendered], ...}
    """
    rendered: dict[Section, list[Rendered]] = {}

    for section, submissions in buckets.items():
        entries = []
        for sub in submissions:
            entries.append(render_entry(sub))
        rendered[section] = entries

    return rendered


def render_report(mod: DigestMod, submissions: list[OpenSubmission]) -> Rendered:
    """the whole digest for one moderator, as (text, html). submissions must already be
    filtered to what they cover"""
    buckets = bucket(submissions, mod.categories)
    entries = render_entries(buckets)
    return render_body(mod.header, entries)
