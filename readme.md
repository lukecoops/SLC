# Simple Local Control (SLC)

## Overview

The **Simple Local Control (SLC)** software is a command-line tool designed to facilitate communication with hardware devices via TCP/IP or serial COM ports. It provides a simple interface for sending commands to read or write data from/to hardware registers, as well as logging the communication session.

### Features
- **Multi-connection support**: Communicates via TCP/IP (network) or serial COM ports.
- **Command flexibility**: Supports read/write commands, delays, continuous data transmission, and command aliasing.
- **Extensive logging**: Logs all communication data into a timestamped CSV file for easy review.

- **Customizable configuration**: Uses a `config.ini` file for pre-loading settings and aliases.

---

## Compatibility

- Cross-platform support for Windows and Linux

---

## How to Use

1. **Run the Script**
   ```bash
   ./slc.exe
   ```
   Upon launch, the software will display the software version and start an interactive session.

2. **Configuration Setup** (Optional)
   - Create a `config.ini` file in the same directory to pre-configure settings:
     ```
     product=TOC
     address=192.168.1.100
     port=10001
     alias_read_all=r 0000; r 0001; r 0002
     ```
   - `product`: The product type (e.g., `TOC` or `ROC`).
   - `address`: IP address or COM port.
   - `port`: Port number (if applicable).
   - `alias_*`: Command aliases for frequently used sequences.

3. **Interactive Commands**
   - **Read Command**: `r <address>`
   - **Write Command**: `w <address> <value>`
   - **Delay Command**: `delay=<seconds>`
   - **Load Command from File**: `<filename>.txt`
   - **Continuous Transmission**: `cont`
   - **Comments**: Add `#` at the beginning of a line for comments.

4. **Example Commands**
   - Single read: `r 1234`
   - Write a value: `w 5678 ABCD`
   - Continuous sending: `cont`
   - Use delay: `r 1234; delay=2; r 5678`
   - Alias from config: `alias_read_all`
   - Load from file commands.txt: `commands`

5. **Exit Continuous Mode**
   - Press `Q` at any time to stop continuous transmissions.

---

## Logs

Logs are saved in the `SLC_LOG` directory as CSV files. The filename format is:
```
slc_command_log_<YYYY-MM-DD_HH-MM-SS>.csv
```
### Log Format
| Timestamp           | Message                        | RW   | Address | Value |
|---------------------|--------------------------------|------|---------|-------|
| 2025-01-27 10:30:00 | Read Complete. Address: 1234  | r    | 1234    |       |
| 2025-01-27 10:31:00 | Write Verified. Address: 5678 | w    | 5678    | ABCD  |

---

## Key Features in Detail

### Input Validation
- Validates IP addresses, COM port names, and hexadecimal values (16-bit).
- Ensures valid port numbers (1-65535).


### Error Handling
- Detects and logs socket timeouts, connection errors, and permission issues when writing logs.

### Command Aliases
- Allows defining shortcuts for complex or repetitive command sequences in `config.ini`.

### Key Press Detection
- Press `Q` to interrupt continuous commands or exit continuous send mode.

---

## Configuration File Example: `config.ini`

```ini
# General Configuration
product=TOC
address=192.168.1.100
port=10001

# Command Aliases
alias_read_all=r 0000; r 0001; r 0002
alias_write_all=w 1234 ABCD; w 5678 9ABC
```