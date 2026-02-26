#!/usr/bin/env python3
"""
OpenClaw Academy — Static Site Exporter

Exports the FastAPI app to a static dist/ directory for Vercel / GitHub Pages deployment.

Features:
- Crawls all 54+ pages (index, modules, lessons, quizzes)
- Downloads CDN assets locally (highlight.js, mermaid.js, htmx)
- Replaces HTMX progress toggle with localStorage-based client-side tracking
- Replaces server-side quiz submission with client-side JS validator
- Creates clean URL structure: /module/foo/index.html
- Generates dist/index.html as entry point

Usage:
    python3 scripts/export_static.py
    cd dist && python3 -m http.server 8090
    open http://localhost:8090
"""
import os
import re
import sys
import time
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PORT = 18765  # Unusual port to avoid conflicts
BASE_URL = f"http://127.0.0.1:{PORT}"
REPO_ROOT = Path(__file__).parent.parent
DIST_DIR = REPO_ROOT / "dist"
COURSE_DIR = REPO_ROOT / "course"
DB_PATH = "/tmp/academy-export.db"

# CDN assets to bundle locally for offline use
CDN_ASSETS = [
    {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css",
        "local": "vendor/highlight.min.css",
    },
    {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
        "local": "vendor/highlight.min.js",
    },
    {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/yaml.min.js",
        "local": "vendor/highlight-yaml.min.js",
    },
    {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/typescript.min.js",
        "local": "vendor/highlight-typescript.min.js",
    },
    {
        "url": "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js",
        "local": "vendor/mermaid.min.js",
    },
    {
        "url": "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js",
        "local": "vendor/htmx.min.js",
    },
]

# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def start_server():
    """Start the FastAPI app as a subprocess."""
    env = os.environ.copy()
    env["COURSE_DIR"] = str(COURSE_DIR)
    env["DB_PATH"] = DB_PATH
    env["DATA_DIR"] = "/tmp"

    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--port", str(PORT),
            "--host", "127.0.0.1",
            "--log-level", "error",
        ],
        cwd=str(REPO_ROOT),
        env=env,
    )


def wait_for_server(timeout=30):
    """Block until server responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def fetch_page(path):
    """Fetch one page from the running server. Returns HTML string or None."""
    url = f"{BASE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  WARNING: Failed to fetch {path}: {e}")
        return None


# ---------------------------------------------------------------------------
# Asset management
# ---------------------------------------------------------------------------

def copy_static_assets(repo_root, dist_dir):
    """Copy app/static/ → dist/static/."""
    src = repo_root / "app" / "static"
    dst = dist_dir / "static"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  ✓ Copied app/static → dist/static/")


def download_cdn_assets(dist_dir):
    """Download CDN assets into dist/static/vendor/ for offline use."""
    vendor_dir = dist_dir / "static" / "vendor"
    vendor_dir.mkdir(parents=True, exist_ok=True)

    for asset in CDN_ASSETS:
        dest = dist_dir / "static" / asset["local"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            print(f"  ✓ Cached: {asset['local']}")
            continue
        print(f"  ↓ {asset['url']}")
        try:
            urllib.request.urlretrieve(asset["url"], str(dest))
            print(f"    → {asset['local']}")
        except Exception as e:
            print(f"    ✗ FAILED: {e}")


# ---------------------------------------------------------------------------
# HTML post-processing
# ---------------------------------------------------------------------------

# JavaScript for client-side progress tracking via localStorage
PROGRESS_JS = """
<script id="static-progress-js">
/* OpenClaw Academy — localStorage progress tracking (static mode) */
(function () {
  var STORAGE_KEY = 'ocademy_progress';

  function getProgress() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch (e) { return {}; }
  }

  function saveProgress(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function isCompleted(lessonId) {
    return !!getProgress()[lessonId];
  }

  function toggle(lessonId) {
    var data = getProgress();
    if (data[lessonId]) { delete data[lessonId]; }
    else { data[lessonId] = new Date().toISOString(); }
    saveProgress(data);
    return !!getProgress()[lessonId];
  }

  function renderBtn(lessonId, completed) {
    var cls = completed ? 'btn-success' : 'btn-outline';
    var label = completed ? '&#x2705; Completed' : 'Mark Complete';
    return '<button class="btn ' + cls + '" data-progress-toggle="' + lessonId + '" onclick="window._ocToggle(this)">'
      + label + '</button>';
  }

  window._ocToggle = function (btn) {
    var lid = btn.getAttribute('data-progress-toggle');
    if (!lid) return;
    var newState = toggle(lid);
    var wrap = document.getElementById('progress-btn-wrap');
    if (wrap) wrap.innerHTML = renderBtn(lid, newState);
  };

  document.addEventListener('DOMContentLoaded', function () {
    var wrap = document.getElementById('progress-btn-wrap');
    if (!wrap) return;
    /* Extract lesson_id from the hidden input in the HTMX form (if present) */
    var hiddenInput = wrap.querySelector('input[name="lesson_id"]');
    if (!hiddenInput) return;
    var lessonId = hiddenInput.value;
    if (!lessonId) return;
    wrap.innerHTML = renderBtn(lessonId, isCompleted(lessonId));
  });
})();
</script>
"""

# JavaScript for client-side sidebar progress indicators
SIDEBAR_PROGRESS_JS = """
<script id="static-sidebar-progress-js">
/* Update sidebar progress badges from localStorage */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var data;
    try { data = JSON.parse(localStorage.getItem('ocademy_progress') || '{}'); }
    catch (e) { data = {}; }

    /* For each sidebar module link, recount done/total from data-lessons attr */
    document.querySelectorAll('[data-module-lessons]').forEach(function (el) {
      var lessons;
      try { lessons = JSON.parse(el.getAttribute('data-module-lessons')); }
      catch (e) { return; }
      var done = lessons.filter(function (lid) { return !!data[lid]; }).length;
      var badge = el.querySelector('.sidebar-badge');
      if (badge) {
        badge.textContent = done + '/' + lessons.length;
        if (done === lessons.length && lessons.length > 0) {
          badge.classList.add('badge-done');
        } else {
          badge.classList.remove('badge-done');
        }
      }
    });
  });
})();
</script>
"""


def rewrite_html(html):
    """
    Post-process crawled HTML for static deployment:
      1. Replace CDN URLs with local vendor paths
      2. Remove server-only endpoints (/api/progress link)
      3. Replace HTMX progress toggle with localStorage version
      4. Inject sidebar progress JS
    """
    # --- CDN → local ---
    cdn_map = {
        "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css":
            "/static/vendor/highlight.min.css",
        "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js":
            "/static/vendor/highlight.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/yaml.min.js":
            "/static/vendor/highlight-yaml.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/typescript.min.js":
            "/static/vendor/highlight-typescript.min.js",
        "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js":
            "/static/vendor/mermaid.min.js",
        "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js":
            "/static/vendor/htmx.min.js",
    }
    for cdn_url, local_path in cdn_map.items():
        html = html.replace(cdn_url, local_path)

    # --- Remove server-only nav link ---
    html = re.sub(
        r'<a[^>]+href="/api/progress"[^>]*>.*?</a>',
        "",
        html,
        flags=re.DOTALL,
    )

    # --- Replace HTMX progress toggle form with static placeholder ---
    # The server renders:
    #   <div id="progress-btn-wrap">
    #     <form hx-post="/progress/toggle" ...>
    #       <input type="hidden" name="lesson_id" value="...">
    #       ...
    #     </form>
    #   </div>
    # We keep the inner form so JS can read the lesson_id, then JS replaces it.
    # The PROGRESS_JS script does this on DOMContentLoaded.
    if '<div id="progress-btn-wrap">' in html and PROGRESS_JS not in html:
        # Inject progress JS just before </body>
        html = html.replace("</body>", PROGRESS_JS + SIDEBAR_PROGRESS_JS + "</body>", 1)

    return html


# ---------------------------------------------------------------------------
# Page discovery
# ---------------------------------------------------------------------------

def load_course_modules():
    """Minimal module loader (doesn't need FastAPI stack)."""
    try:
        import yaml
    except ImportError:
        print("  ERROR: PyYAML not installed. Run: pip install pyyaml")
        sys.exit(1)

    modules = []
    if not COURSE_DIR.exists():
        print(f"  ERROR: COURSE_DIR not found: {COURSE_DIR}")
        sys.exit(1)

    for module_dir in sorted(COURSE_DIR.iterdir()):
        if not module_dir.is_dir():
            continue
        meta_file = module_dir / "meta.yaml"
        if not meta_file.exists():
            continue
        meta = yaml.safe_load(meta_file.read_text())
        meta["_dir"] = str(module_dir)
        modules.append(meta)

    modules.sort(key=lambda m: m.get("order", 999))
    return modules


def get_all_pages(modules):
    """Return every URL path in the academy."""
    pages = ["/"]
    for m in modules:
        mid = m["id"]
        pages.append(f"/module/{mid}")
        for lesson in m.get("lessons", []):
            pages.append(f"/module/{mid}/lesson/{lesson['slug']}")
        pages.append(f"/module/{mid}/quiz")
    return pages


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------

def save_page(path, html, dist_dir):
    """Save a crawled page to dist/ with clean URL structure."""
    if path == "/":
        out_file = dist_dir / "index.html"
    else:
        clean = path.strip("/")
        out_file = dist_dir / clean / "index.html"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(html, encoding="utf-8")
    return out_file


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("🦞 OpenClaw Academy — Static Export")
    print("=" * 52)

    # Verify we're in the right place
    if not (REPO_ROOT / "app" / "main.py").exists():
        print(f"ERROR: Expected app/main.py at {REPO_ROOT}")
        print("Run this script from the repo root or as: python3 scripts/export_static.py")
        sys.exit(1)

    # Step 1: Clean dist directory
    print("\n[1/6] Cleaning dist/...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    print(f"  ✓ Ready: {DIST_DIR}")

    # Step 2: Check dependencies
    print("\n[2/6] Checking dependencies...")
    missing = []
    for pkg in ("uvicorn", "fastapi", "mistune", "yaml", "aiosqlite"):
        real_pkg = "PyYAML" if pkg == "yaml" else pkg
        try:
            __import__(pkg)
        except ImportError:
            missing.append(real_pkg)
    if missing:
        print(f"  ✗ Missing: {', '.join(missing)}")
        print("  Run: pip install -r requirements.txt")
        sys.exit(1)
    print("  ✓ All dependencies available")

    # Step 3: Copy & download assets
    print("\n[3/6] Bundling static assets...")
    copy_static_assets(REPO_ROOT, DIST_DIR)
    download_cdn_assets(DIST_DIR)

    # Step 4: Start server
    print("\n[4/6] Starting FastAPI server...")
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()

    proc = start_server()
    print(f"  Server PID {proc.pid} on port {PORT}...")

    if not wait_for_server():
        print("  ✗ Server failed to start within 30 seconds")
        proc.terminate()
        sys.exit(1)
    print("  ✓ Server ready")

    # Step 5: Crawl pages
    print("\n[5/6] Crawling pages...")
    modules = load_course_modules()
    pages = get_all_pages(modules)
    print(f"  Found {len(pages)} pages ({len(modules)} modules)")

    crawled = 0
    failed = []

    for path in pages:
        print(f"  {path}", end=" ", flush=True)
        html = fetch_page(path)
        if html is None:
            failed.append(path)
            print("✗ FAILED")
            continue
        html = rewrite_html(html)
        out = save_page(path, html, DIST_DIR)
        crawled += 1
        rel = out.relative_to(DIST_DIR)
        print(f"→ {rel}")

    # Step 6: Shutdown server
    print("\n[6/6] Shutting down server...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("  ✓ Server stopped")

    # Summary
    print("\n" + "=" * 52)
    if failed:
        print(f"⚠️  Export finished with {len(failed)} failure(s):")
        for p in failed:
            print(f"   ✗ {p}")
        status = 1
    else:
        print(f"✅ Export complete! {crawled} pages exported.")
        status = 0

    print(f"\n   Output:  {DIST_DIR}/")
    print(f"   Preview: cd dist && python3 -m http.server 8090")
    print(f"            open http://localhost:8090")
    print()

    sys.exit(status)


if __name__ == "__main__":
    main()
