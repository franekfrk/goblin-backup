# Recovery and restore

## 1. Obtain the repository and password

Mount the share using your OS tools. Put the password file on a trusted recovery machine with mode 600. Do not place it in the repository. Paths below are examples; use your actual values.

```bash
export RESTIC_REPOSITORY=/mnt/backup/Goblin-Backup-Encrypted
export RESTIC_PASSWORD_FILE=/etc/goblin-backup/repository.key
sudo --preserve-env=RESTIC_REPOSITORY,RESTIC_PASSWORD_FILE restic snapshots
```

Encrypted metadata contains the source machine paths. Inspect the chosen snapshot, rather than assuming that its paths match the examples:

```bash
sudo --preserve-env=RESTIC_REPOSITORY,RESTIC_PASSWORD_FILE restic ls SNAPSHOT_ID
sudo --preserve-env=RESTIC_REPOSITORY,RESTIC_PASSWORD_FILE restic check --read-data
```

Use an explicit snapshot ID. `latest` can select the wrong snapshot in a shared repository.

## 2. Restore into an empty directory

```bash
sudo --preserve-env=RESTIC_REPOSITORY,RESTIC_PASSWORD_FILE restic restore SNAPSHOT_ID --target /mnt/restore-review
```

Source paths are preserved. For example, `state_dir=/var/lib/goblin-backup-public` produces:

```
/mnt/restore-review/var/lib/goblin-backup-public/current/
  system/          -> original /
  home/            -> original /home
  dane/            -> original /dane (excluding configured Nextcloud folder)
  boot/            -> original /boot
  efi/             -> original /boot/efi
  recovery-info/   -> VM XML, package list, filesystem information, test probe
```

The original Goblin predecessor used `/var/lib/goblin-backup/current/` instead. Inspect your snapshot to choose the correct prefix.

Restore a few important files and compare their hashes/content before relying on the copy. Files excluded from a backup cannot be recovered from it.

## 3. Restore a VM

Keep the target VM off. Preserve any existing disk before replacing anything. Restore the disk file, VM XML and applicable UEFI NVRAM/TPM state from their backed-up locations. Review XML paths, storage pools and permissions. Define the VM using `virsh define` only after verifying the XML. Restore correct ownership and SELinux contexts using the target host's libvirt conventions. Test boot and application data before removing old copies. Do not start two copies with the same network identity against production services.

## 4. Full workstation recovery

This backup is not an image containing the partition table and LUKS headers. Boot Fedora rescue media, create the required partitions/LUKS containers/filesystems and Btrfs subvolumes, mount them, then copy restored `system`, `home`, `dane`, `boot` and `efi` into the corresponding destinations while preserving ownership, ACLs and xattrs. Update `/etc/fstab` and `/etc/crypttab` for the target UUIDs, regenerate initramfs/bootloader using the appropriate Fedora instructions, and restore SELinux contexts. Verify excluded cloud data can be downloaded again. These steps depend on the actual disk layout; do not blindly apply generic formatting commands.

Prefer practicing recovery on a spare disk or isolated VM before a real incident. A successful small probe restore is not a full disaster recovery test.

## Interrupted backup / snapshot cleanup

1. Check `systemctl status goblin-backup` and make sure the task and its restic processes have stopped.
2. Inspect root-owned `state_dir/staging.json`. It lists the exact mounts and snapshots created by this run.
3. Unmount **only those staging bind mounts**, in reverse order, using `umount`.
4. Check each snapshot with `btrfs subvolume show PATH`, then delete **only those snapshots**, using `btrfs subvolume delete PATH`.
5. Ensure no mounts remain below `state_dir/current` (`findmnt -R`). Move the remaining staging directory aside or remove it only after inspection. Do not delete original source subvolumes.
6. If the VM was running before the failed run, check its state and start it if necessary. Abrupt process termination or host failure can prevent automatic restart.
7. A stale restic lock can be removed with `restic unlock` **only after verifying no backup/check/restore is using that repository**.
8. Start a new run. Restic reuses already uploaded content. This version does not provide an automatic resume or pruning command.

Never delete repository contents manually to free a lock. Never run recursive removal on a directory which still contains bind mounts.
