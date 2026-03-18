# pstack_flamegen

A zero-dependency browser app that generates interactive flamegraph SVGs from raw pstack samples. Built for support engineers who need to quickly visualize hundreds of pstack captures.

**No installation required** — just open `index.html` in your browser. All processing happens locally in the browser; no data leaves your machine.

## Features

- **Zero setup** — single HTML file, no server, no Python, no dependencies to install
- **Drag-and-drop upload** — drop individual `.out` files, ZIP archives, or tar.gz files
- **Interactive flamegraph** — zoom, search, and hover for details (powered by d3-flame-graph)
- **SVG download** — export the flamegraph as an SVG file
- **Time range display** — automatically detects timestamps from collect-stacks.sh filenames and shows earliest/latest collection time and duration
- **Smart filtering** — automatically skips `.err` files, only processes `.out` files
- **Multi-format parsing** — supports Linux pstack, GDB backtrace, and jstack output
- **Dark theme UI**

## Quick Start

```bash
# Clone the repo
git clone https://github.com/rephillips/pstack_flamegen.git
cd pstack_flamegen

# Open in your browser
open index.html        # macOS
xdg-open index.html    # Linux
start index.html       # Windows
```

That's it. No `pip install`, no server to run.

## Usage

1. Open `index.html` in your browser
2. Drag and drop your pstack `.out` files onto the upload area (or click to browse)
   - Supports individual `.out` files from collect-stacks.sh
   - Supports `.zip` archives containing multiple pstack files
   - Supports `.tar.gz` archives
   - `.err` files are automatically filtered out
3. The flamegraph renders automatically after upload
4. **Search** — type a function name in the search bar to highlight matching frames
5. **Zoom** — click any frame to zoom into that subtree
6. **Reset Zoom** — click the Reset Zoom button to return to the full view
7. **Download SVG** — click Download SVG to save the flamegraph as a file
8. **New Upload** — click New Upload to start over with different files

## Collecting Pstacks on Splunk Enterprise

This repo includes the `collect-stacks.sh` script for collecting pstack samples from the main splunkd process.

### Steps

1. **Copy the script to the Splunk host:**

   ```bash
   cd /opt/splunk/bin
   # Copy collect-stacks.sh from this repo to the host
   vi collect-stacks.sh
   ```

2. **Give the file executable permissions:**

   ```bash
   chmod +x collect-stacks.sh
   ```

3. **Install elfutils** (not required on Splunk Cloud):

   ```bash
   yum install elfutils
   ```

4. **Create the output directory:**

   ```bash
   cd /tmp
   mkdir splunk
   ```

   The default output directory in the script is `/tmp/splunk`.

5. **Execute the script:**

   ```bash
   ./collect-stacks.sh
   ```

   The default script parameters are to collect a stack every 0.5 seconds, 1000 times. These defaults are sufficient.

6. **Once the script finishes, tar the directory created inside `/tmp/splunk`:**

   ```bash
   cd /tmp/splunk
   tar -zcvf archive-name.tar.gz source-directory-name
   ```

   > **Note:** It is normal to see `.err` files for each `.out` file. The flamegraph generator automatically skips `.err` files.

7. **SCP from cloud instance to local machine:**

   ```bash
   scp <user>@<host>:/tmp/<archive-name>.tar.gz .
   ```

8. **Generate a diag once pstack collection is finished** (not required on Splunk Cloud):

   ```bash
   cd $SPLUNK_HOME/bin
   ./splunk diag
   ```

9. **Upload the archive or `.out` files to the Flamegraph Generator** to visualize the results.

## Sample Data

The `sample_data/` directory contains 500 synthetic pstack samples modeled after Splunk Enterprise thread stacks. Use these to test the app:

1. Open `index.html` in your browser
2. Select all files in `sample_data/` and drag them onto the upload area
3. Or zip them first: `cd sample_data && zip ../samples.zip *.out && cd ..` then upload the ZIP

## Supported Pstack Formats

**Linux pstack / GDB backtrace:**
```
Thread 1 (Thread 0x7f4b2c0d0700 (LWP 12345)):
#0  0x00007f4b2a1e3840 in __poll () from /lib64/libc.so.6
#1  0x00007f4b2b5a1234 in Splunkd::mainLoop () from /opt/splunk/lib/libsplunk.so
#2  0x00007f4b2b5b0000 in main () from /opt/splunk/bin/splunkd
```

**Java jstack:**
```
"main" #1 prio=5 os_prio=0 tid=0x00007f... nid=0x1 runnable
   at com.example.App.processRequest(App.java:42)
   at com.example.App.main(App.java:10)
```

## License

Apache License 2.0
