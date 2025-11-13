import typer
import os
from . import utils
from .utils import _

app = typer.Typer(no_args_is_help=True)


@app.command(name="status")
def status():
    """
    Checks the status of the Marzban service
    """
    utils.rich_console.print(_("Checking Marzban service status..."))
    os.system("sudo systemctl status enhanced-marzban")


@app.command(name="logs")
def logs():
    """
    Displays the logs of the Marzban service
    """
    utils.rich_console.print(_("Showing Marzban service logs..."))
    os.system("sudo journalctl -u enhanced-marzban -f")


@app.command(name="restart")
def restart():
    """
    Restarts the Marzban service
    """
    utils.rich_console.print(_("Restarting Marzban service..."))
    os.system("sudo systemctl restart enhanced-marzban")


@app.command(name="start")
def start():
    """
    Starts the Marzban service
    """
    utils.rich_console.print(_("Starting Marzban service..."))
    os.system("sudo systemctl start enhanced-marzban")


@app.command(name="stop")
def stop():
    """
    Stops the Marzban service
    """
    utils.rich_console.print(_("Stopping Marzban service..."))
    os.system("sudo systemctl stop enhanced-marzban")


@app.command(name="fail2ban-status")
def fail2ban_status():
    """
    Checks the status of the Fail2ban service
    """
    utils.rich_console.print(_("Checking Fail2ban service status..."))
    os.system("sudo systemctl status fail2ban")


@app.command(name="fail2ban-ban")
def fail2ban_ban(
    ip: str = typer.Option(..., "--ip", help=_("IP address to ban"))
):
    """
    Bans an IP address with Fail2ban
    """
    utils.rich_console.print(_("Banning IP address {ip}...").format(ip=ip))
    os.system(f"sudo fail2ban-client set marzban-violations banip {ip}")


@app.command(name="fail2ban-unban")
def fail2ban_unban(
    ip: str = typer.Option(..., "--ip", help=_("IP address to unban"))
):
    """
    Unbans an IP address with Fail2ban
    """
    utils.rich_console.print(_("Unbanning IP address {ip}...").format(ip=ip))
    os.system(f"sudo fail2ban-client set marzban-violations unbanip {ip}")
