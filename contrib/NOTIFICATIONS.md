# KDE desktop notifications (optional)

`notification-event.py` is a root-owned systemd hook which queues only result metadata in `/var/lib/goblin-backup-notifications/latest.json` (world-readable, no secrets). It does not read backup contents or logs. Install it root-owned in `/usr/local/libexec/goblin-backup-notification-event`.

Add `ExecStopPost=/usr/local/libexec/goblin-backup-notification-event` to the backup service's `[Service]`. It uses systemd's `SERVICE_RESULT`. For failures before ExecStopPost (for example failed mount dependencies), add `OnFailure=goblin-backup-notify-failure.service` to `[Unit]`; that oneshot service runs the hook with `--failure`.

Run `notification-client.py` as the intended desktop user from a user service/timer every minute. Requires `notify-send` (`libnotify` package on Fedora). It shows silent desktop notifications and remembers delivery in `~/.local/state/goblin-backup-notifications/ack`. If the desktop isn't running, the latest event remains queued for the next login. Multiple unattended events collapse into the latest event; full history remains in the system journal. Only actual backup success is described as successful.

These notifications appear on the Fedora desktop, not directly on a disconnected Windows client or phone. Desktop notification history and Do Not Disturb behavior are controlled by KDE.
