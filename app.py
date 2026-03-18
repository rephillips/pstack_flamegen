#!/usr/bin/env python3
"""
Flamegraph Generator — Web app to visualize pstack samples as interactive flamegraphs.

Upload raw pstack output files (or a ZIP of them) and get an interactive,
zoomable, searchable flamegraph rendered in the browser.
"""

import io
import os
import re
import zipfile
from collections import Counter
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload


def parse_pstack_output(text):
    """
    Parse raw pstack/gdb/jstack output into a list of stack traces.

    Handles multiple formats:
    - Linux pstack: Thread 1 (Thread 0x7f...): / #0  0x00... in func()
    - GDB bt: #0  func (args) at file.c:123
    - jstack: "thread-name" #1 daemon prio=5 / at com.example.Class.method(File.java:123)

    Returns a list of stacks, where each stack is a list of function names
    (deepest frame first, i.e., leaf at index 0).
    """
    stacks = []
    current_stack = []
    in_thread = False

    for line in text.splitlines():
        line = line.strip()

        # Detect thread boundaries
        if re.match(r'^Thread \d+', line) or \
           re.match(r'^#\d+\s+(daemon\s+)?prio=', line) or \
           re.match(r'^".*"\s+#?\d+', line) or \
           re.match(r'^-{3,}\s+lwp', line, re.IGNORECASE) or \
           re.match(r'^LWP\s+\d+', line):
            if current_stack:
                stacks.append(current_stack)
                current_stack = []
            in_thread = True
            continue

        # Skip empty lines
        if not line:
            if current_stack:
                stacks.append(current_stack)
                current_stack = []
            in_thread = False
            continue

        # Parse stack frames
        func_name = None

        # Format: #N  0x... in func_name () from /lib/...
        m = re.match(r'^#\d+\s+0x[0-9a-fA-F]+\s+in\s+(.+?)(?:\s*\(.*?\))?\s*(?:from\s+|at\s+|$)', line)
        if m:
            func_name = m.group(1).strip()

        # Format: #N  func_name (args) at file.c:123
        if not func_name:
            m = re.match(r'^#\d+\s+(?:0x[0-9a-fA-F]+\s+in\s+)?(.+?)\s*\(', line)
            if m:
                func_name = m.group(1).strip()

        # Format: at com.example.Class.method(File.java:123)  (jstack)
        if not func_name:
            m = re.match(r'^\s*at\s+(.+?)\s*\(', line)
            if m:
                func_name = m.group(1).strip()

        # Format: simple function name line (no frame number)
        if not func_name and in_thread:
            m = re.match(r'^([a-zA-Z_][\w:.]+(?:::[\w]+)*)', line)
            if m and len(m.group(1)) > 2:
                func_name = m.group(1).strip()

        if func_name:
            # Clean up function names
            func_name = re.sub(r'\s*\[.*?\]', '', func_name)
            func_name = func_name.strip()
            if func_name and func_name not in ('??', '???'):
                current_stack.append(func_name)

    # Don't forget the last stack
    if current_stack:
        stacks.append(current_stack)

    return stacks


def stacks_to_folded(stacks):
    """
    Convert parsed stacks to folded format for flamegraph rendering.

    Each stack is reversed so the root is on the left and leaf on the right,
    then joined with semicolons. Identical stacks are counted.

    Returns a list of dicts: [{"stack": "root;parent;child;leaf", "count": N}, ...]
    """
    counter = Counter()
    for stack in stacks:
        if not stack:
            continue
        # Reverse: pstack gives deepest first, flamegraph wants root first
        reversed_stack = list(reversed(stack))
        key = ';'.join(reversed_stack)
        counter[key] += 1

    result = []
    for stack_str, count in counter.most_common():
        result.append({"stack": stack_str, "count": count})

    return result


def folded_to_d3_hierarchy(folded_data):
    """
    Convert folded stack data into a nested hierarchy suitable for d3-flame-graph.

    Returns a tree structure:
    {
        "name": "root",
        "value": 0,
        "children": [
            {"name": "func_a", "value": 5, "children": [...]},
            ...
        ]
    }
    """
    root = {"name": "all", "value": 0, "children": []}

    for entry in folded_data:
        frames = entry["stack"].split(";")
        count = entry["count"]
        node = root

        for frame in frames:
            # Find or create child
            child = None
            for c in node.get("children", []):
                if c["name"] == frame:
                    child = c
                    break
            if child is None:
                child = {"name": frame, "value": 0, "children": []}
                node.setdefault("children", []).append(child)
            child["value"] += count
            node = child

    # Clean up empty children arrays
    def cleanup(node):
        if not node.get("children"):
            node.pop("children", None)
        else:
            for c in node["children"]:
                cleanup(c)
    cleanup(root)

    # Set root value to total samples
    root["value"] = sum(e["count"] for e in folded_data)

    return root


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and return flamegraph data."""
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    all_stacks = []
    file_count = 0

    for f in files:
        filename = f.filename or ''

        # Handle ZIP files
        if filename.lower().endswith('.zip'):
            try:
                zip_data = io.BytesIO(f.read())
                with zipfile.ZipFile(zip_data) as zf:
                    for name in zf.namelist():
                        if name.endswith('/'):
                            continue  # skip directories
                        try:
                            text = zf.read(name).decode('utf-8', errors='replace')
                            stacks = parse_pstack_output(text)
                            if stacks:
                                all_stacks.extend(stacks)
                                file_count += 1
                        except Exception:
                            continue
            except zipfile.BadZipFile:
                return jsonify({"error": f"Invalid ZIP file: {filename}"}), 400
        else:
            # Regular text file
            try:
                text = f.read().decode('utf-8', errors='replace')
                stacks = parse_pstack_output(text)
                if stacks:
                    all_stacks.extend(stacks)
                    file_count += 1
            except Exception as e:
                return jsonify({"error": f"Error reading {filename}: {str(e)}"}), 400

    if not all_stacks:
        return jsonify({"error": "No valid stack traces found in uploaded files"}), 400

    folded = stacks_to_folded(all_stacks)
    hierarchy = folded_to_d3_hierarchy(folded)

    return jsonify({
        "data": hierarchy,
        "stats": {
            "files": file_count,
            "total_stacks": len(all_stacks),
            "unique_stacks": len(folded),
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"Flamegraph Generator running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
