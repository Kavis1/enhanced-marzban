from typing import Optional, List

import typer
from rich.table import Table

from app.db import GetDB, crud
from app.db.models import User
from app.utils.system import readable_size
from app.models.user import UserCreate, UserModify

from . import utils
from .utils import _

app = typer.Typer(no_args_is_help=True)


@app.command(name="list")
def list_users(
    offset: Optional[int] = typer.Option(None, *utils.FLAGS["offset"]),
    limit: Optional[int] = typer.Option(None, *utils.FLAGS["limit"]),
    username: Optional[List[str]] = typer.Option(None, *utils.FLAGS["username"], help=_("Search by username(s)")),
    search: Optional[str] = typer.Option(None, *utils.FLAGS["search"], help=_("Search by username/note")),
    status: Optional[crud.UserStatus] = typer.Option(None, *utils.FLAGS["status"]),
    admins: Optional[List[str]] = typer.Option(None, *utils.FLAGS["admin"], help=_("Search by owner admin's username(s)"))
):
    """
    Displays a table of users

    NOTE: Sorting is not currently available.
    """
    with GetDB() as db:
        users: list[User] = crud.get_users(
            db=db, offset=offset, limit=limit,
            usernames=username, search=search, status=status,
            admins=admins
        )

        utils.print_table(
            table=Table(
                "ID", "Username", "Status", "Used traffic",
                "Data limit", "Reset strategy", "Expires at", "Owner",
            ),
            rows=[
                (
                    str(user.id),
                    user.username,
                    user.status.value,
                    readable_size(user.used_traffic),
                    readable_size(user.data_limit) if user.data_limit else "Unlimited",
                    user.data_limit_reset_strategy.value,
                    utils.readable_datetime(user.expire, include_time=False),
                    user.admin.username if user.admin else ''
                )
                for user in users
            ]
        )


@app.command(name="set-owner")
def set_owner(
    username: str = typer.Option(None, *utils.FLAGS["username"], prompt=True),
    admin: str = typer.Option(None, "--admin", "--owner", prompt=True, help=_("Admin's username")),
    yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help=_("Skips confirmations"))
):
    """
    Transfers user's ownership

    NOTE: This command needs additional confirmation for users who already have an owner.
    """
    with GetDB() as db:
        user: User = utils.raise_if_falsy(
            crud.get_user(db, username=username), _('User "{username}" not found.').format(username=username))

        dbadmin = utils.raise_if_falsy(
            crud.get_admin(db, username=admin), _('Admin "{admin}" not found.').format(admin=admin))

        # Ask for confirmation if user already has an owner
        if user.admin and not yes_to_all and not typer.confirm(
            _('{username}\'s current owner is "{owner}". Are you sure about transferring its ownership to "{admin}"?').format(
                username=username, owner=user.admin.username, admin=admin
            )
        ):
            utils.error(_("Aborted."))

        crud.set_owner(db, user, dbadmin)

        utils.success(_('{username}\'s owner successfully set to "{admin}".').format(username=username, admin=admin))


@app.command(name="create")
def create_user(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    password: str = typer.Option(..., "--password", prompt=True, hide_input=True, confirmation_prompt=True),
    data_limit: int = typer.Option(0, "--data-limit", help=_("Data limit in bytes")),
    expire: int = typer.Option(0, "--expire", help=_("Expire date in days from now")),
):
    """
    Creates a new user
    """
    with GetDB() as db:
        user_in = UserCreate(
            username=username,
            password=password,
            data_limit=data_limit,
            expire=expire,
        )
        user = crud.create_user(
            db=db,
            user=user_in,
        )
        utils.success(_('User "{username}" created successfully.').format(username=user.username))


@app.command(name="delete")
def delete_user(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help=_("Skips confirmations"))
):
    """
    Deletes a user
    """
    with GetDB() as db:
        user = utils.raise_if_falsy(
            crud.get_user(db, username=username), _('User "{username}" not found.').format(username=username))

        if not yes_to_all and not typer.confirm(
            _('Are you sure you want to delete user "{username}"?').format(username=username)
        ):
            utils.error(_("Aborted."))

        crud.remove_user(db, user)
        utils.success(_('User "{username}" deleted successfully.').format(username=username))


@app.command(name="update")
def update_user(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    new_username: str = typer.Option(None, "--new-username", help=_("New username")),
    password: str = typer.Option(None, "--password", help=_("New password")),
    data_limit: int = typer.Option(None, "--data-limit", help=_("Data limit in bytes")),
    expire: int = typer.Option(None, "--expire", help=_("Expire date in days from now")),
    status: crud.UserStatus = typer.Option(None, *utils.FLAGS["status"]),
):
    """
    Updates a user
    """
    with GetDB() as db:
        user = utils.raise_if_falsy(
            crud.get_user(db, username=username), _('User "{username}" not found.').format(username=username))

        update_data = {
            "username": new_username,
            "password": password,
            "data_limit": data_limit,
            "expire": expire,
            "status": status,
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}
        user_in = UserModify(**update_data)
        user = crud.update_user(
            db=db,
            dbuser=user,
            modify=user_in,
        )
        utils.success(_('User "{username}" updated successfully.').format(username=user.username))


@app.command(name="view")
def view_user(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True)
):
    """
    Displays user details
    """
    with GetDB() as db:
        user = utils.raise_if_falsy(
            crud.get_user(db, username=username), _('User "{username}" not found.').format(username=username))

        utils.print_table(
            table=Table(
                "Attribute", "Value",
            ),
            rows=[
                ("ID", str(user.id)),
                ("Username", user.username),
                ("Status", user.status.value),
                ("Used traffic", readable_size(user.used_traffic)),
                ("Data limit", readable_size(user.data_limit) if user.data_limit else "Unlimited"),
                ("Reset strategy", user.data_limit_reset_strategy.value),
                ("Expires at", utils.readable_datetime(user.expire, include_time=False)),
                ("Owner", user.admin.username if user.admin else ''),
            ]
        )
