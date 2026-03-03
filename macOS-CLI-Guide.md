# macOS Command-Line Interface (CLI) Complete Guide

**For macOS M1 Systems**  
**Last Updated: March 2026**

This comprehensive guide contains all built-in macOS CLI tools organised by functional category for quick reference and practical use.

---

## Table of Contents

1. [File & Directory Management](#file--directory-management)
2. [System Administration](#system-administration)
3. [Security & Permissions](#security--permissions)
4. [Network & Connectivity](#network--connectivity)
5. [Disk & Storage Management](#disk--storage-management)
6. [Audio & Media Processing](#audio--media-processing)
7. [Process & Performance Monitoring](#process--performance-monitoring)
8. [User & Group Management](#user--group-management)
9. [Package & Software Management](#package--software-management)
10. [Automation & Scripting](#automation--scripting)
11. [Power Management](#power-management)
12. [Clipboard & Text Utilities](#clipboard--text-utilities)
13. [Development Tools](#development-tools)
14. [Spotlight & Search](#spotlight--search)
15. [Keyboard Shortcuts](#keyboard-shortcuts)
16. [Essential Basic Commands](#essential-basic-commands)

---

## File & Directory Management

### Navigation & Inspection

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `ls` | List directory contents | `ls -la` (detailed list with hidden files) |
| `cd` | Change directory | `cd ~/Documents` |
| `pwd` | Print working directory | `pwd` |
| `find` | Search for files and directories | `find . -name "*.txt"` |
| `mdfind` | Spotlight search from CLI | `mdfind "kMDItemFSName == '*report*'"` |
| `mdls` | Display metadata attributes | `mdls document.pdf` |
| `GetFileInfo` | Get HFS+ file attributes | `GetFileInfo myfile.txt` |

### File Operations

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `touch` | Create empty file | `touch newfile.txt` |
| `mkdir` | Make directory | `mkdir -p path/to/dir` |
| `cp` | Copy files | `cp source.txt dest.txt` |
| `mv` | Move or rename | `mv old.txt new.txt` |
| `rm` | Remove files | `rm -rf directory/` |
| `ditto` | Copy with metadata preservation | `ditto /source /dest` |
| `cat` | Display file contents | `cat file.txt` |
| `less` | View file with pagination | `less logfile.txt` |
| `head` | Display first lines | `head -n 20 file.txt` |
| `tail` | Display last lines | `tail -f logfile.txt` (follow mode) |
| `nano` | Simple text editor | `nano file.txt` |
| `vim` | Advanced text editor | `vim file.txt` |

### Advanced File Operations

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `chmod` | Change permissions | `chmod 755 script.sh` |
| `chown` | Change ownership | `sudo chown user:group file.txt` |
| `chflags` | Change file flags | `chflags uchg important.doc` (make immutable) |
| `setfile` | Set file attributes | `SetFile -a V hiddenfile.txt` (make invisible) |
| `xattr` | Extended attributes utility | `xattr -l file.txt` |
| `dot_clean` | Remove `.DS_Store` files | `dot_clean /Volumes/USBDrive` |
| `textutil` | Manipulate text files | `textutil -convert txt file.doc` |
| `sips` | Image processing | `sips -z 600 800 input.jpg --out output.jpg` |

---

## System Administration

### System Information

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `sw_vers` | Show macOS version | `sw_vers` |
| `system_profiler` | System configuration report | `system_profiler SPHardwareDataType` |
| `ioreg` | View I/O kit registry | `ioreg -l` |
| `uname` | System information | `uname -a` |
| `whoami` | Current username | `whoami` |
| `hostname` | Display system hostname | `hostname` |
| `date` | Display/set date and time | `date "+%Y-%m-%d %H:%M:%S"` |

### System Configuration

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `systemsetup` | Configure system settings | `sudo systemsetup -setcomputersleep 30` |
| `scutil` | System configuration utility | `scutil --get HostName` |
| `nvram` | Manipulate firmware variables | `sudo nvram boot-args="-v"` |
| `csrutil` | Configure SIP (System Integrity Protection) | `csrutil status` |
| `defaults` | Modify preference files | `defaults write com.apple.finder ShowHidden -bool true` |
| `plutil` | Property list utility | `plutil -convert xml1 settings.plist` |
| `shutdown` | Shutdown or restart | `sudo shutdown -h now` |
| `reboot` | Restart system | `sudo reboot` |

### Service Management

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `launchctl` | Manage daemons and agents | `launchctl list` |
| `caffeinate` | Prevent system sleep | `caffeinate -t 3600` (1 hour) |
| `purge` | Clear disk cache | `sudo purge` |
| `kickstart` | Configure Apple Remote Desktop | `sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -activate` |

---

## Security & Permissions

### Security Tools

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `fdesetup` | FileVault setup utility | `sudo fdesetup enable` |
| `security` | Manage keychains and certificates | `security list-keychains` |
| `codesign` | Create/verify code signatures | `codesign -v /Applications/App.app` |
| `spctl` | Security policy control | `spctl --status` |
| `pfctl` | Packet filter (firewall) control | `sudo pfctl -e` |
| `csrutil` | System Integrity Protection | `csrutil status` |
| `tccutil` | Privacy database management | `tccutil reset All` |

### Permission Management

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `chmod` | Change file permissions | `chmod 755 file.sh` |
| `chown` | Change ownership | `sudo chown user:group file` |
| `chflags` | Change file flags | `chflags hidden file.txt` |
| `ls -ld` | Display directory permissions | `ls -ld ~` |

---

## Network & Connectivity

### Network Configuration

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `networksetup` | Configure network settings | `networksetup -setdnsservers Wi-Fi 8.8.8.8` |
| `scselect` | Switch network locations | `scselect "Office"` |
| `airport` | Manage Wi-Fi | `airport -s` (scan networks) |
| `ifconfig` | Network interface configuration | `ifconfig en0` |
| `networkQuality` | Network performance testing | `networkQuality` |

### Network Diagnostics

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `ping` | Test network connectivity | `ping google.com` |
| `traceroute` | Trace network path | `traceroute google.com` |
| `dig` | DNS lookup | `dig google.com` |
| `nslookup` | DNS query | `nslookup google.com` |
| `netstat` | Network statistics | `netstat -an` |
| `lsof` | List open files/connections | `lsof -i :8080` |
| `dscacheutil` | Directory service cache utility | `sudo dscacheutil -flushcache` |
| `wdutil` | Wireless diagnostics utility | `wdutil info` |

---

## Disk & Storage Management

### Disk Operations

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `diskutil` | Disk utilities | `diskutil list` |
| `hdiutil` | Manipulate disk images | `hdiutil create -srcfolder /path -format UDZO image.dmg` |
| `df` | Disk space usage | `df -h` |
| `du` | Directory space usage | `du -sh *` |
| `asr` | Apple Software Restore (clone disks) | `sudo asr restore --source image.dmg --target /Volumes/Drive` |
| `pdisk` | Apple Partition Table editor | `pdisk /dev/disk0 -dump` |
| `mkfile` | Create file with specific size | `mkfile 100m testfile.dat` |
| `drutil` | CD/DVD burner control | `drutil tray eject` |

### Time Machine

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `tmutil` | Time Machine utility | `tmutil listbackups` |
| | Enable/disable Time Machine | `sudo tmutil enable` |
| | Start backup | `tmutil startbackup` |

### Storage Optimisation

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `trimforce` | Enable TRIM for third-party SSDs | `sudo trimforce enable` |
| `purge` | Clear disk cache | `sudo purge` |

---

## Audio & Media Processing

### Audio Tools

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `afplay` | Play audio files | `afplay notification.wav` |
| `afinfo` | Display audio file info | `afinfo song.m4a` |
| `afconvert` | Convert audio formats | `afconvert input.aiff -o output.mp3 -f MP3` |
| `say` | Text-to-speech | `say "Hello, world!"` |
| | Save to audio file | `say -o greeting.aiff "Welcome"` |

### Image Processing

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `sips` | Scriptable image processing | `sips -z 600 800 input.jpg --out output.jpg` |
| | Convert format | `sips -s format png input.jpg --out output.png` |
| `screencapture` | Capture screenshots | `screencapture screen.jpg` |
| | Capture window | `screencapture -w -T5 window.png` |
| `qlmanage` | Quick Look management | `qlmanage -p document.pdf` |

---

## Process & Performance Monitoring

### Process Management

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `ps` | List processes | `ps aux` |
| `top` | Monitor processes (interactive) | `top` |
| `htop` | Enhanced process viewer | `htop` (requires installation) |
| `kill` | Terminate process | `kill -9 PID` |
| `killall` | Kill processes by name | `killall Safari` |
| `pgrep` | Find processes by name | `pgrep -fl Chrome` |

### Performance Monitoring

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `powermetrics` | Power and performance stats | `sudo powermetrics --samplers cpu_power` |
| `fs_usage` | Filesystem activity monitor | `sudo fs_usage` |
| `execsnoop` | Monitor process execution | `sudo execsnoop` |
| `opensnoop` | Monitor file opens | `sudo opensnoop` |
| `iosnoop` | Monitor I/O events | `sudo iosnoop` |
| `taskpolicy` | Set process resource policies | `taskpolicy -b script.sh` |

---

## User & Group Management

### User Operations

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `whoami` | Current username | `whoami` |
| `id` | User/group information | `id username` |
| `users` | List logged-in users | `users` |
| `last` | Show login history | `last` |
| `passwd` | Change user password | `passwd` |
| `dscl` | Directory Service command line | `dscl . list /Users` |
| `dsenableroot` | Enable/disable root user | `sudo dsenableroot` |
| `createhomedir` | Create home directories | `sudo createhomedir -c` |

### Group Management

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `dseditgroup` | Edit groups | `sudo dseditgroup -o edit -a username -t user admin` |
| `dsmemberutil` | View user/group rights | `dsmemberutil checkmembership -U user -G group` |
| `groups` | Show user's groups | `groups username` |

---

## Package & Software Management

### Package Tools

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `installer` | Install macOS packages | `sudo installer -pkg package.pkg -target /` |
| `pkgbuild` | Build installer packages | `pkgbuild --root /path --identifier com.example.pkg example.pkg` |
| `pkgutil` | Package manager utility | `pkgutil --pkgs` (list installed packages) |
| | Forget package | `sudo pkgutil --forget com.example.pkg` |
| `lsbom` | List bill of materials | `lsbom /var/db/receipts/com.example.pkg.bom` |
| `softwareupdate` | Manage software updates | `softwareupdate -l` (list available) |
| | Install updates | `sudo softwareupdate -i -a` |

### Developer Tools

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `xcode-select` | Manage developer tools | `xcode-select --install` |
| `brew` | Homebrew package manager | `brew install wget` (if Homebrew installed) |

---

## Automation & Scripting

### Scripting Tools

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `osascript` | Execute AppleScript | `osascript -e 'display dialog "Hello"'` |
| `osacompile` | Compile AppleScript | `osacompile -o MyApp.app script.scpt` |
| `automator` | Run Automator workflow | `automator workflow.workflow` |
| `shortcuts` | Manage Shortcuts | `shortcuts list` |
| | Run shortcut | `shortcuts run "Resize Images"` |
| `cron` | Schedule tasks | `crontab -e` |
| `at` | Schedule one-time tasks | `at now + 1 hour` |
| `bash` | Bash shell | `bash script.sh` |
| `zsh` | Z shell (default macOS shell) | `zsh` |

---

## Power Management

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `pmset` | Power management settings | `sudo pmset displaysleep 15` |
| | View settings | `pmset -g` |
| | Disable sleep | `sudo pmset sleep 0` |
| `caffeinate` | Prevent sleep | `caffeinate -t 7200` (2 hours) |
| | Keep display on | `caffeinate -d` |
| `shutdown` | Shutdown system | `sudo shutdown -h now` |
| | Scheduled shutdown | `sudo shutdown -h +60` (in 60 mins) |

---

## Clipboard & Text Utilities

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `pbcopy` | Copy to clipboard | `cat file.txt \| pbcopy` |
| `pbpaste` | Paste from clipboard | `pbpaste > clipboard.txt` |
| `pbs` | Pasteboard server | `killall pbs` (restart clipboard) |
| `grep` | Search text patterns | `grep "error" logfile.txt` |
| `sed` | Stream editor | `sed 's/old/new/g' file.txt` |
| `awk` | Text processing | `awk '{print $1}' data.txt` |
| `wc` | Word/line count | `wc -l file.txt` |
| `sort` | Sort lines | `sort file.txt` |
| `uniq` | Remove duplicates | `sort file.txt \| uniq` |

---

## Development Tools

### Code Signing & Building

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `codesign` | Sign/verify code | `codesign -s "Developer ID" App.app` |
| `xcodebuild` | Build Xcode projects | `xcodebuild -project MyApp.xcodeproj` |
| `xcode-select` | Manage Xcode tools | `xcode-select --print-path` |
| `otool` | Object file display | `otool -L /usr/bin/ls` |
| `nm` | Symbol table viewer | `nm executable` |
| `ldd` | List dynamic dependencies | `otool -L binary` |

### Kernel Extensions

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `kextstat` | Kernel extension status | `kextstat` |
| `kextfind` | Find kernel extensions | `kextfind -b com.example.driver` |
| `kextunload` | Unload kernel extension | `sudo kextunload Extension.kext` |

---

## Spotlight & Search

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `mdfind` | Spotlight search | `mdfind "kMDItemFSName == '*report*'"` |
| `mdls` | Display metadata attributes | `mdls document.pdf` |
| `mdimport` | Import into Spotlight index | `mdimport /path/to/folder` |
| `mdutil` | Manage Spotlight indexing | `sudo mdutil -i off /Volumes/Drive` |
| | Rebuild index | `sudo mdutil -E /` |
| `lsregister` | Launch Services database | `/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user` |

---

## Keyboard Shortcuts

### Terminal Navigation

| Shortcut | Description |
|----------|-------------|
| `Control + C` | Cancel current command |
| `Control + D` | Exit terminal/logout |
| `Control + L` | Clear screen |
| `Control + A` | Move to start of line |
| `Control + E` | Move to end of line |
| `Control + U` | Delete from cursor to start |
| `Control + K` | Delete from cursor to end |
| `Control + W` | Delete word before cursor |
| `Control + R` | Search command history |
| `Tab` | Auto-complete |
| `Command + T` | New terminal tab |
| `Command + N` | New terminal window |
| `Command + K` | Clear screen |
| `Up/Down Arrow` | Navigate command history |
| `Option + Left/Right` | Move cursor by word |

---

## Essential Basic Commands

### Core Unix Commands

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `man` | Manual pages | `man ls` |
| `which` | Locate command | `which python3` |
| `whereis` | Locate binary/source | `whereis python` |
| `type` | Command type | `type ls` |
| `history` | Command history | `history \| grep "git"` |
| `clear` | Clear terminal | `clear` or `Control + L` |
| `echo` | Display text | `echo "Hello"` |
| `export` | Set environment variable | `export PATH=$PATH:/new/path` |
| `env` | Show environment variables | `env` |
| `printenv` | Print environment | `printenv PATH` |
| `alias` | Create command alias | `alias ll='ls -la'` |
| `source` | Execute script in current shell | `source ~/.zshrc` |
| `wait4path` | Wait for path to become available | `wait4path /Volumes/Drive` |

### File Viewing

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `cat` | Concatenate/view files | `cat file.txt` |
| `less` | View with pagination | `less file.txt` |
| `more` | Simple pagination | `more file.txt` |
| `head` | First lines | `head -n 10 file.txt` |
| `tail` | Last lines | `tail -f logfile.txt` |
| `open` | Open with default app | `open file.pdf` |
| | Open URL | `open https://example.com` |
| | Open with specific app | `open -a TextEdit file.txt` |

### Compression & Archives

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `tar` | Archive utility | `tar -czf archive.tar.gz folder/` |
| | Extract | `tar -xzf archive.tar.gz` |
| `gzip` | Compress files | `gzip file.txt` |
| `gunzip` | Decompress | `gunzip file.txt.gz` |
| `zip` | Create zip archive | `zip -r archive.zip folder/` |
| `unzip` | Extract zip | `unzip archive.zip` |

---

## Useful Aliases for .zshrc

Add these to your `~/.zshrc` file for quick access:

```bash
# Navigation shortcuts
alias ..='cd ..'
alias ...='cd ../..'
alias ~='cd ~'

# List commands
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'

# Git shortcuts (if using git)
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'

# System maintenance
alias cleanup='sudo purge && brew cleanup'
alias update='sudo softwareupdate -i -a; brew update && brew upgrade'

# Network
alias flushdns='sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder'
alias myip='curl ifconfig.me'

# File operations
alias cp='cp -iv'
alias mv='mv -iv'
alias rm='rm -iv'
alias mkdir='mkdir -pv'

# Processes
alias psg='ps aux | grep -v grep | grep -i -e VSZ -e'

# Show/hide hidden files in Finder
alias showhidden='defaults write com.apple.finder AppleShowAllFiles -bool true && killall Finder'
alias hidehidden='defaults write com.apple.finder AppleShowAllFiles -bool false && killall Finder'
```

---

## Configuration Profiles Management

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `profiles` | Manage configuration profiles | `profiles -P` (list profiles) |
| | Install profile | `sudo profiles -I -F profile.mobileconfig` |
| | Remove profile | `sudo profiles -R -p identifier` |

---

## Miscellaneous Utilities

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `tab2space` | Convert tabs to spaces | `tab2space file.txt` |
| `textutil` | Text file manipulation | `textutil -convert txt file.docx` |
| `cupsfilter` | Convert using CUPS filters | `cupsfilter input.pdf > output.pcl` |
| `atsutil` | Font system utility | `atsutil databases -remove` |
| `sharing` | Configure file sharing | `sharing -l` |
| `serverinfo` | macOS Server information | `serverinfo --version` |
| `bless` | Set startup disk | `sudo bless --mount /Volumes/Drive --setBoot` |
| `wait4path` | Wait for path availability | `wait4path /Volumes/USBDrive` |
| `ufs.util` | UFS filesystem utility | `ufs.util -m disk2s1` |
| `ntfs.util` | NTFS filesystem utility | `ntfs.util -m disk2s1` |
| `ReportCrash` | Crash reporting | `launchctl unload -w /System/Library/LaunchAgents/com.apple.ReportCrash.plist` |

---

## Tips for CLI Usage on macOS M1

### Performance Optimisation

1. **Use native ARM64 binaries** when available
2. **Monitor Rosetta 2 usage**: Check if apps run under Rosetta with `ps aux | grep Rosetta`
3. **Leverage unified memory**: M1 shares memory between CPU/GPU

### Shell Configuration

Default shell is **zsh** (not bash). Configuration file: `~/.zshrc`

```bash
# Open configuration
nano ~/.zshrc

# Reload configuration
source ~/.zshrc
```

### Path Management

```bash
# View current PATH
echo $PATH

# Add to PATH (in ~/.zshrc)
export PATH="/usr/local/bin:$PATH"

# Add Homebrew (M1 location)
export PATH="/opt/homebrew/bin:$PATH"
```

### Homebrew on M1

Installation location differs from Intel Macs:
- **M1 (ARM)**: `/opt/homebrew/`
- **Intel**: `/usr/local/`

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add to PATH (add to ~/.zshrc)
export PATH="/opt/homebrew/bin:$PATH"
```

---

## Command Syntax Basics

### Redirection & Piping

```bash
# Output to file (overwrite)
command > output.txt

# Append to file
command >> output.txt

# Pipe output to another command
command1 | command2

# Redirect errors
command 2> error.log

# Redirect both output and errors
command > output.txt 2>&1
```

### Background & Job Control

```bash
# Run in background
command &

# List jobs
jobs

# Bring to foreground
fg %1

# Send to background
bg %1

# Pause current process
Control + Z
```

### Command Chaining

```bash
# Run sequentially (regardless of success)
command1; command2

# Run if previous succeeds
command1 && command2

# Run if previous fails
command1 || command2
```

---

## Getting Help

### Documentation Commands

| Command | Description | Example |
|---------|-------------|---------|
| `man` | Manual pages | `man ls` |
| `info` | Info documentation | `info grep` |
| `help` | Shell built-in help | `help cd` |
| `command --help` | Quick help | `ls --help` |
| `command -h` | Short help flag | `grep -h` |
| `apropos` | Search man pages | `apropos network` |
| `whatis` | Brief description | `whatis ls` |

### Online Resources

- **Official Apple Documentation**: https://support.apple.com/guide/terminal/
- **SS64 Command Reference**: https://ss64.com/osx/
- **Homebrew**: https://brew.sh/
- **GitHub Repository**: https://github.com/netmute/macos_cli_tools

---

## Security Best Practices

1. **Use `sudo` carefully** - Only when necessary
2. **Verify commands** - Use `man` before running unknown commands
3. **Check permissions** - Use `ls -la` to verify file permissions
4. **Keep system updated** - Run `softwareupdate -l` regularly
5. **Enable FileVault** - Use `fdesetup` for disk encryption
6. **Verify code signatures** - Use `codesign -v` on downloaded apps
7. **Monitor processes** - Use `top` or `ps aux` to check running processes

---

## Summary of Most Useful Commands

For daily CLI usage on macOS M1, these are essential:

**Navigation & Files**:
- `ls`, `cd`, `pwd`, `mkdir`, `rm`, `cp`, `mv`, `find`, `grep`

**System Info**:
- `top`, `df -h`, `du -sh`, `sw_vers`, `system_profiler`

**Network**:
- `ping`, `ifconfig`, `networksetup`, `dig`, `curl`

**Process Management**:
- `ps aux`, `kill`, `killall`, `top`

**Utilities**:
- `open`, `pbcopy`, `pbpaste`, `screencapture`, `say`, `caffeinate`

**Package Management**:
- `brew install`, `softwareupdate -l`

---

**End of macOS CLI Guide**

*This document provides a comprehensive reference for command-line operations on macOS. For detailed information on specific commands, use `man command` or visit the official documentation.*
