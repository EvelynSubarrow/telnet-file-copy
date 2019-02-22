# telnet-file-copy
This is a simple utility to copy files onto a linux host running a telnet server, where other means
aren't available. This tool should only be used as a last resort - it's slow, and offers no
integrity guarantees.

On the remote end, all that's necessary is an `echo` command which supports the `-e` and `-n` flags.
If a host has any of `md5sum`, `sha256sum` or `sha512sum`, the most preferable will be used to verify
the integrity of the transfer, and if `base64` is present, this will be used for the transfer instead of
`echo`.
