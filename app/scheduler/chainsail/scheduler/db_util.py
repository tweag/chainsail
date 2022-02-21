""""Database helper functions"""
import logging

import click
from chainsail.scheduler.core import db
from chainsail.scheduler.db import TblUsers

logger = logging.getLogger("chainsail.scheduler")


@click.command()
@click.option("--email", required=True)
def add_user(email: str):
    logger.info(f"Granting job access to user {email}...")
    user = TblUsers.query.filter_by(email=email).one_or_none()
    if user is None:
        user = TblUsers(email=email)
        db.session.add(user)
    user.is_allowed = True
    db.session.commit()


@click.command()
@click.option("--email", required=True)
def remove_user(email: str):
    logger.info(f"Revoking job access for user {email}...")
    user = TblUsers.query.filter_by(email=email).one_or_none()
    if user is None:
        logger.info(f"User was not found, no access to revoke.")
    user.is_allowed = False
    db.session.commit()
