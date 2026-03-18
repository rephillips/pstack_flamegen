# pstack_flamegen

A web app that generates interactive flamegraph SVGs from raw pstack samples. Built for support engineers who need to quickly visualize hundreds of pstack captures.

## Features

- **Drag-and-drop upload** — drop individual pstack files or a ZIP archive
- **Interactive flamegraph** — zoom, search, and hover for details (powered by d3-flame-graph)
- **SVG download** — export the flamegraph as an SVG file
- **Multi-format parsing** — supports Linux pstack, GDB backtrace, and jstack output
- **Dark theme UI**

## Requirements

- Python 3.8+
- Flask

## Quick Start

```bash
# Clone the repo
git clone https://github.com/rephillips/pstack_flamegen.git
cd pstack_flamegen

# Install dependencies
pip install -r requirements.txt

# Start the app
python3 app.py
```

Open your browser to **http://localhost:5050**

## Usage

1. Open the app in your browser
2. Drag and drop your pstack sample files onto the upload area (or click to browse)
   - Supports individual `.txt`, `.log`, `.out`, `.pstack`, `.trace` files
   - Supports `.zip` archives containing multiple pstack files
3. The flamegraph renders automatically after upload
4. **Search** — type a function name in the search bar to highlight matching frames
5. **Zoom** — click any frame to zoom into that subtree
6. **Reset Zoom** — click the Reset Zoom button to return to the full view
7. **Download SVG** — click Download SVG to save the flamegraph
8. **New Upload** — click New Upload to start over with different files

## Sample Data

The `sample_data/` directory contains 500 synthetic pstack samples modeled after Splunk Enterprise thread stacks. Use these to test the app:

1. Start the app with `python3 app.py`
2. Select all files in `sample_data/` and drag them onto the upload area
3. Or zip them first: `cd sample_data && zip ../samples.zip *.txt && cd ..` then upload the ZIP

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

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `PORT` | `5050` | Port to run the web server on |

## License

Apache License 2.0
