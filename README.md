# Goblin Backup

Encrypted file backups for Fedora/Btrfs workstations with an optional libvirt Windows VM.
Uses read-only Btrfs snapshots and restic, including a full repository data check and a small restore test.

**Status: early version.** The predecessor scripts successfully backed up a real workstation.
This configurable rewrite has configuration/exclusion tests and a temporary restic encryption/restore integration test, but has not yet completed an end-to-end backup/restore on another machine. Test on disposable data first.

## What it does

1. Verifies the destination mount and its exact source before writing.
2. Gracefully shuts down a running VM (never force-kills it).
3. Creates read-only snapshots of the configured Btrfs subvolumes.
4. Restarts the VM if this run shut it down.
5. Copies configured boot directories and records package/filesystem/VM information.
6. Encrypts, deduplicates and compresses data through restic.
7. Reads repository data back and restores a small probe file.
8. Removes this run's snapshots only after successful verification.
9. With `keep_last = 4`, keeps the last four snapshots for this hostname and prunes unreferenced data, only after successful verification. This includes predecessor snapshots with different paths/tags: use a dedicated repository per machine. Set `keep_last = 0` to disable deletion.

This is a **file backup, not a bootable disk image**. The restore probe does not prove that an entire OS or VM can boot after restoration. Boot/EFI copies are taken live; snapshots are taken sequentially, not atomically across disks. Applications other than the configured VM are captured in a crash-consistent state, not necessarily application-consistent state.

## Installation (Fedora)

Requirements: Python 3.11+, Btrfs, restic, libvirt if using a VM, and an already mounted backup destination (e.g. a CIFS automount). All `sources` must be Btrfs subvolumes. Nested subvolumes and other filesystems are not recursively captured; list every required subvolume separately. Confirm your VM disks and any UEFI NVRAM/TPM state are covered.

```bash
sudo dnf install restic btrfs-progs python3 util-linux coreutils libvirt-client
sudo install -m 755 bin/goblin-backup /usr/local/bin/goblin-backup
sudo install -m 755 bin/goblin-backup-status /usr/local/bin/goblin-backup-status
sudo install -d -m 700 /etc/goblin-backup
sudo install -m 600 examples/config.toml /etc/goblin-backup/config.toml
sudoedit /etc/goblin-backup/config.toml
sudo goblin-backup check
```

Edit the destination mount/source, VM name and source subvolumes. The example IP is a documentation placeholder, not a real server.
Mount credentials belong in a separate root-owned file outside Git. Configure CIFS using your OS tools; this project does not manage shares or save SMB passwords.

The default example excludes `/dane/Nextcloud`. Remove that entry if you need it backed up. Review all exclusions and ensure snapshot parents are on the same Btrfs filesystem as their sources. The restic password directory is excluded automatically. Do not put extra copies of that password elsewhere in source directories.

## Run

Save work in the VM before starting. No unattended schedule is installed.

```bash
sudo systemd-run --unit=goblin-backup --collect /usr/local/bin/goblin-backup backup
sudo goblin-backup status
sudo journalctl -u goblin-backup -f
```

To stop:

```bash
sudo systemctl stop goblin-backup
```

An interrupted or failed run is **not a verified backup**. Staging snapshots may remain; read [recovery and cleanup](docs/RESTORE.md) before another run. Do not run two instances. The tool also takes a local lock.

## Encryption key: save separately

On first backup a random password is generated at the configured `password_file` (root-owned, mode 600). It is never copied to the destination. A pre-existing repository without its password file causes an error rather than silently generating a replacement.

Store an independent copy in your password manager or a separate protected USB device. **Losing both the workstation and this key makes the backup unrecoverable.** Private GitHub repositories are not key storage. Never commit a key, SMB credentials, actual config, VM image, backup data or logs.

The destination can be read by a server administrator, but restic content is encrypted. The server can still delete the repository; encryption does not prevent deletion. RAID mirror does not replace a backup.

## Desktop notifications

Optional silent KDE notifications report success, errors or cancellation and queue the latest result until next login. See [contrib/NOTIFICATIONS.md](contrib/NOTIFICATIONS.md).

## Restore

See [docs/RESTORE.md](docs/RESTORE.md) for listing snapshots, restoring files/VM and rebuilding a workstation. Restore into a separate empty directory first. Restoring a system requires Fedora rescue media and knowledge of LUKS/Btrfs/bootloader recovery.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile bin/goblin-backup
```

The restic integration test creates and verifies a temporary local repository. No tests shut down VMs, mount filesystems, create Btrfs snapshots or contact a backup server. `check` validates config/dependencies without starting a backup.

MIT license: [LICENSE](LICENSE).
