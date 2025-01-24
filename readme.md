# Simple Local Control (SLC)

## Overview

This script provides a client-server communication interface for interacting with BAE peoducts (DRx, TOC, ROC and DWG). It supports reading and writing operations using a structured command format over TCP sockets.

---

## Getting Started

### Prerequisites

- Python
- Computer on the same network as product

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lukecoops/SLC.git
   cd SLC
### Usage

1.  **Run the script**:

   ```bash
    python slc.py
```
2.  **Enter product**:
   ```
    Enter one of the following products: `DRX`, `TOC`, `ROC`, `DWG`: 
```
3.  **Provide IP address and port**:
    ```
    IP Address:
    Port:
4.  **Enter a command**:

    -   Read Command:

        `r [address]`

        Example:

        `r 1F34`

    -   Write Command:

        `w [address] [val]`

        Example:

        `w 1F34 AB12`


Command Format
--------------

-   `r [address]`: Reads data from the specified 16-bit hexadecimal address.
-   `w [address] [value]`: Writes a 16-bit hexadecimal value to the specified address.

**Note**: Both `address` and `value` must be valid 16-bit hexadecimal values (e.g., `1F34`, `AB12`).

* * * * *
Example Interaction
-------------------
```
SLC v1.0.0
Enter Product (DRX, TOC, ROC, DWG): TOC
Connected to server at 127.0.0.1:65432
Enter a command in '[r/w] [address] [val]': r 1F34
Command: r, Address: 1F34
Data word: 0xAB12 (43858)
Enter a command in '[r/w] [address] [val]': w 1F34 AB12
Command: w, Address: 1F34, Value: AB12
Server response: Write Completed
Enter a command in '[r/w] [address] [val]':
```
* * * * *