"""processes notifications"""
import logging
import json
from typing import Callable

from google.pubsub import ReceivedMessage

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE
from app.config import settings
from app.email import send_email
from app.email_content import get_submission_info, render_email
from app.schema import NotificationParams, SimplifiedNotification, ConsolidatedNotifications, EmailTask, NotificationType, CommentData, PromoteData, NewPropData, PropRespData, UserContact, SubEmailData
from app.moderators import get_all_moderators, get_recipient_ids_for_categories, get_mod_emails

logger = logging.getLogger(__name__)


def _parse_message(payload)-> tuple[NotificationParams, SimplifiedNotification]:
    """turn pubsub payload insto structured data, raises an error if data is badly formed"""
    full_note = NotificationParams.model_validate(payload)

    match full_note.action:
        case NotificationType.COMMENT:
            data = CommentData.model_validate(full_note.data)
        case NotificationType.NEW_PROP:
            data = NewPropData.model_validate(full_note.data)
        case NotificationType.PROMOTE:
            data = PromoteData.model_validate(full_note.data)
        case NotificationType.PROP_RESP:
            data = PropRespData.model_validate(full_note.data)
        case _:
            logger.error(f"unhandled action type: {full_note.action}, skipping message")
            raise ValueError(f"unhandled action: {full_note.action}")

    simple_note=SimplifiedNotification(time=full_note.time, user_id=full_note.user_id, data=data)
    return full_note, simple_note

def _convert_messages(messages: list[ReceivedMessage], ack_fn: Callable[[list[str]], None]) -> dict[int, ConsolidatedNotifications]:
    """manages turning the recieved pubsub messages into consolidated data on submissions with notifications"""

    all_notifications: dict[int, ConsolidatedNotifications]={} #tracks all notifications for each submission

    #convert each message and store in lists
    for msg in messages:

        #validation and error handling
        try:
            payload = json.loads(msg.message.data.decode("utf-8"))
            full_note, simple_note = _parse_message(payload)
        except Exception as e:
            logger.error(f"[PARSE FAILURE] {e} — msg: {msg.message.data}")
            ack_fn([msg.ack_id]) #ack immediately — won't be fixed on retry
            continue

        #convert and store
        categories: set[Category]=set()
        for cat in full_note.categories:
            try:
                categories.add(CATEGORIES_ACTIVE[cat])
            except KeyError:
                logger.error(f"unknown category: {cat}, skipping")

        id=full_note.submission_id
        sub_notes = all_notifications.get(id, ConsolidatedNotifications(submission_id=id))
        sub_notes.ack_ids.append(msg.ack_id) #ack only after successful email send
        sub_notes.user_ids.add(full_note.user_id)
        sub_notes.changes.append(simple_note)
        sub_notes.categories.update(categories)

        all_notifications[id]=sub_notes

    return all_notifications

def _build_email_tasks(all_notifications: dict[int, ConsolidatedNotifications]) -> tuple[list[EmailTask], dict[int, UserContact]]:
    if not all_notifications:
        logger.info("No notifications to process")
        return [], {}

    #collect all the categories and emails
    archives, cats = get_all_moderators()

    all_categories: set[Category] = set()
    for notifications in all_notifications.values():
        all_categories.update(notifications.categories)

    per_cat, ids_to_email = get_recipient_ids_for_categories(all_categories, archives, cats)

    #include actor user IDs so one query covers everyone
    actor_ids = {c.user_id for n in all_notifications.values() for c in n.changes}
    ids_to_contact = get_mod_emails(ids_to_email | actor_ids)

    #build individual email tasks
    tasks = []
    for sub_id, notifications in all_notifications.items():
        email_ids: set[int] = set()
        reply_ids: set[int] = set()
        #everyone to email
        for cat in notifications.categories:
            e, r = per_cat.get(cat.id, (set(), set()))
            email_ids.update(e)
            reply_ids.update(r)
        # don't email the sole actor about their own changes
        if len(notifications.user_ids) == 1:
            sole_actor = next(iter(notifications.user_ids))
            email_ids.discard(sole_actor)

        to_emails = [ids_to_contact[uid].email for uid in email_ids if uid in ids_to_contact]
        reply_to = [ids_to_contact[uid].email for uid in reply_ids if uid in ids_to_contact]

        missing = (email_ids | reply_ids) - ids_to_contact.keys()
        if missing:
            logger.error(f"submission {sub_id}: no tapir_users row for moderator ids {missing}")

        if not to_emails:
            logger.info(f"submission {sub_id}: no recipients after exclusions, skipping")
            continue

        #email data
        tasks.append(EmailTask(
            submission_id=sub_id,
            to_emails=to_emails,
            reply_to_emails=reply_to,
            notifications=notifications,
        ))
    return tasks, ids_to_contact


def _send_email_tasks(
    email_tasks: list[EmailTask],
    sub_infos: dict[int, SubEmailData],
    ids_to_contact: dict[int, UserContact],
    ack_fn: Callable[[list[str]], None],
) -> None:
    """render and send emails, acking each submission only after its email sends"""

    if settings.REDIRECT_EMAILS:
        logger.info(f"REDIRECT_EMAILS active — all emails → {settings.REDIRECT_RECIPIENT}")

    sent = 0
    for task in email_tasks:
        sub = sub_infos.get(task.submission_id)
        if sub is None:
            logger.error(f"submission {task.submission_id}: not found in DB, skipping")
            continue  # don't ack — will redeliver

        #render email content — failure skips this task (no ack)
        try:
            body_text, body_html = render_email(task, sub, ids_to_contact)
        except Exception:
            logger.exception(f"Failed to render email for submission {task.submission_id}, skipping")
            continue

        #send email — failure skips ack (will redeliver)
        try:
            submitter = sub.submitter_name or f"user {sub.submitter_id}"
            subject = f"Action Required: arXiv submission submit/{task.submission_id} to {sub.submission_categories} by {submitter}"
            accepted = send_email(
                to_emails=task.to_emails,
                subject=subject,
                body=body_text,
                html_body=body_html,
                submission_id=task.submission_id,
                reply_to_emails=task.reply_to_emails,
            )
            ack_fn(task.notifications.ack_ids)  # ack on success or all-refused (terminal)
            if accepted:
                sent += 1
        except Exception:
            logger.exception(f"Failed to send email for submission {task.submission_id}, will redeliver")

    logger.info(f"Sent {sent}/{len(email_tasks)} email(s) to relay")


def process_messages(messages: list[ReceivedMessage], ack_fn: Callable[[list[str]], None]) -> None:
    """handles the overall message processing"""

    #turn messages into data — parse failures acked immediately via ack_fn
    all_notifications = _convert_messages(messages, ack_fn)

    #if sending is disabled, ack everything and stop — no DB calls, no rendering
    if not settings.SEND_EMAILS:
        for notifications in all_notifications.values():
            ack_fn(notifications.ack_ids)
        logger.info(f"Email sending disabled — acked {len(all_notifications)} notification group(s)")
        return

    if not all_notifications:
        logger.info("No valid notifications after parsing, nothing to send")
        return

    #determine who to email what
    email_tasks, ids_to_contact = _build_email_tasks(all_notifications)

    #ack any submissions skipped due to no valid recipients (terminal — retrying won't help)
    task_sub_ids = {t.submission_id for t in email_tasks}
    skipped_sub_ids = []
    for sub_id, notifications in all_notifications.items():
        if sub_id not in task_sub_ids:
            ack_fn(notifications.ack_ids)
            skipped_sub_ids.append(sub_id)

    if not email_tasks:
        logger.warning(f"No emails to send — submissions with no recipients: {sorted(skipped_sub_ids)}")
        return

    if skipped_sub_ids:
        logger.info(f"Skipped submissions (no recipients): {sorted(skipped_sub_ids)}")

    #fetch submission data — if batch query fails, skip all sends (will redeliver)
    try:
        sub_infos = get_submission_info({t.submission_id for t in email_tasks})
    except Exception:
        logger.exception("Failed to fetch submission info, skipping all email sends")
        return

    #send emails
    _send_email_tasks(email_tasks, sub_infos, ids_to_contact, ack_fn)
    logger.info(f"Processed {len(messages)} messages, built {len(email_tasks)} email task(s).")
    return