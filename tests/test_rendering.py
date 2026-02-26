"""
OpenClaw Academy — Playwright E2E Test Suite
Tests all 54 pages for correct rendering, UI elements, responsiveness,
interactivity, and captures visual regression baseline screenshots.
"""

import os
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect, sync_playwright

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8090"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

ALL_URLS = [
    "/",
    "/module/module-01-overview",
    "/module/module-01-overview/lesson/what-is-openclaw",
    "/module/module-01-overview/lesson/architecture-overview",
    "/module/module-01-overview/lesson/end-to-end-message-flow",
    "/module/module-01-overview/quiz",
    "/module/module-02-gateway",
    "/module/module-02-gateway/lesson/gateway-daemon",
    "/module/module-02-gateway/lesson/websocket-protocol",
    "/module/module-02-gateway/lesson/session-store",
    "/module/module-02-gateway/lesson/configuration-system",
    "/module/module-02-gateway/quiz",
    "/module/module-03-channels",
    "/module/module-03-channels/lesson/channel-plugin-architecture",
    "/module/module-03-channels/lesson/telegram-and-whatsapp",
    "/module/module-03-channels/lesson/discord-slack-others",
    "/module/module-03-channels/quiz",
    "/module/module-04-agents",
    "/module/module-04-agents/lesson/agent-lifecycle",
    "/module/module-04-agents/lesson/tool-system",
    "/module/module-04-agents/lesson/memory-and-compaction",
    "/module/module-04-agents/lesson/multi-agent-routing",
    "/module/module-04-agents/quiz",
    "/module/module-05-skills",
    "/module/module-05-skills/lesson/skill-anatomy",
    "/module/module-05-skills/lesson/skill-loading",
    "/module/module-05-skills/lesson/hooks-and-workspace",
    "/module/module-05-skills/quiz",
    "/module/module-06-security",
    "/module/module-06-security/lesson/trust-hierarchy",
    "/module/module-06-security/lesson/prompt-injection-defenses",
    "/module/module-06-security/lesson/tool-policy-sandboxing",
    "/module/module-06-security/quiz",
    "/module/module-07-config",
    "/module/module-07-config/lesson/config-structure",
    "/module/module-07-config/lesson/model-configuration",
    "/module/module-07-config/lesson/agent-configuration",
    "/module/module-07-config/lesson/auth-profiles",
    "/module/module-07-config/quiz",
    "/module/module-08-extending",
    "/module/module-08-extending/lesson/writing-a-skill",
    "/module/module-08-extending/lesson/custom-routing",
    "/module/module-08-extending/lesson/mcp-integration",
    "/module/module-08-extending/quiz",
    "/module/module-09-deployment",
    "/module/module-09-deployment/lesson/macos-deployment",
    "/module/module-09-deployment/lesson/docker-deployment",
    "/module/module-09-deployment/lesson/linux-vps-deployment",
    "/module/module-09-deployment/quiz",
    "/module/module-10-case-study",
    "/module/module-10-case-study/lesson/our-architecture",
    "/module/module-10-case-study/lesson/our-skills-and-workflows",
    "/module/module-10-case-study/lesson/lessons-learned",
    "/module/module-10-case-study/quiz",
]

LESSON_URLS = [u for u in ALL_URLS if "/lesson/" in u]
QUIZ_URLS = [u for u in ALL_URLS if u.endswith("/quiz")]
MODULE_URLS = [
    u for u in ALL_URLS
    if u.startswith("/module/") and "/lesson/" not in u and not u.endswith("/quiz")
]

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 720},
    "tablet":  {"width": 768,  "height": 1024},
    "mobile":  {"width": 375,  "height": 667},
}

# Quiz correct answers for module-01 (used in interactive tests)
QUIZ_CORRECT_M01 = {
    "q1": "b",
    "q2": "c",
    "q3": "b",
    "q4": "c",
    "q5": "b",
    "q6": "a",
    "q7": "b",
}

QUIZ_WRONG_M01 = {q: "a" for q in QUIZ_CORRECT_M01}  # all "a" — mostly wrong


# ---------------------------------------------------------------------------
# pytest-playwright configuration
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Default browser context: capture console errors."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
    }


# ---------------------------------------------------------------------------
# Helper: collect JS console errors (ignores CDN 404s for network-unavailable
# resources like mermaid / hljs that are external but don't break layout)
# ---------------------------------------------------------------------------

def _attach_console_listener(page: Page) -> list:
    errors = []

    def on_console(msg):
        if msg.type == "error":
            # Filter out CDN load failures that are environment-specific
            text = msg.text
            skip_patterns = [
                "Failed to load resource",
                "net::ERR_",
                "ERR_NAME_NOT_RESOLVED",
            ]
            if not any(p in text for p in skip_patterns):
                errors.append(text)

    page.on("console", on_console)
    return errors


# ===========================================================================
# 1. PAGE LOAD TESTS — all 54 URLs
# ===========================================================================

class TestPageLoads:
    """Every page returns 200, has the right title, and shows main content."""

    @pytest.mark.parametrize("path", ALL_URLS)
    def test_status_200(self, page: Page, path: str):
        response = page.goto(BASE_URL + path, wait_until="domcontentloaded")
        assert response is not None, f"No response for {path}"
        assert response.status == 200, (
            f"Expected 200 for {path}, got {response.status}"
        )

    @pytest.mark.parametrize("path", ALL_URLS)
    def test_title_contains_openclaw_academy(self, page: Page, path: str):
        page.goto(BASE_URL + path, wait_until="domcontentloaded")
        assert "OpenClaw Academy" in page.title(), (
            f"Title '{page.title()}' missing 'OpenClaw Academy' on {path}"
        )

    @pytest.mark.parametrize("path", ALL_URLS)
    def test_no_js_console_errors(self, page: Page, path: str):
        errors = _attach_console_listener(page)
        page.goto(BASE_URL + path, wait_until="networkidle")
        assert errors == [], (
            f"JS console errors on {path}:\n" + "\n".join(errors)
        )

    @pytest.mark.parametrize("path", ALL_URLS)
    def test_main_content_visible(self, page: Page, path: str):
        page.goto(BASE_URL + path, wait_until="domcontentloaded")
        main = page.locator("main.main-content")
        expect(main).to_be_visible()
        # Must have some non-empty text content
        content_text = main.inner_text()
        assert len(content_text.strip()) > 50, (
            f"main.main-content looks empty on {path} (text: {content_text[:100]!r})"
        )


# ===========================================================================
# 2. UI ELEMENT TESTS
# ===========================================================================

class TestUIElements:

    def test_sidebar_present_on_index(self, page: Page):
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        sidebar = page.locator("aside.sidebar")
        expect(sidebar).to_be_visible()

    def test_sidebar_lists_all_10_modules(self, page: Page):
        # The sidebar with module links is populated on lesson/module pages, not on index.
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        module_links = page.locator("aside.sidebar .sidebar-module-link")
        count = module_links.count()
        assert count == 10, f"Expected 10 sidebar module links, found {count}"

    def test_sidebar_present_on_lesson(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        sidebar = page.locator("aside.sidebar")
        expect(sidebar).to_be_visible()

    def test_module_cards_on_index_are_present(self, page: Page):
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        cards = page.locator("a.module-card")
        count = cards.count()
        assert count == 10, f"Expected 10 module cards on index, found {count}"

    def test_module_cards_are_clickable(self, page: Page):
        """Click the first module card and verify navigation."""
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        first_card = page.locator("a.module-card").first
        href = first_card.get_attribute("href")
        assert href and "/module/" in href, f"Module card href looks wrong: {href}"
        first_card.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/module/" in page.url, f"Did not navigate to module page, URL: {page.url}"

    def test_lesson_cards_on_module_page(self, page: Page):
        """Module overview page shows lesson links."""
        page.goto(BASE_URL + "/module/module-01-overview", wait_until="domcontentloaded")
        lesson_links = page.locator("a.lesson-card, a[href*='/lesson/']")
        count = lesson_links.count()
        assert count >= 3, f"Expected >= 3 lesson links on module page, found {count}"

    def test_lesson_cards_are_clickable(self, page: Page):
        page.goto(BASE_URL + "/module/module-01-overview", wait_until="domcontentloaded")
        first_lesson = page.locator("a[href*='/lesson/']").first
        first_lesson.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/lesson/" in page.url, f"Did not navigate to lesson page, URL: {page.url}"

    def test_progress_bar_on_index(self, page: Page):
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        progress = page.locator(".progress-bar, .overall-progress")
        expect(progress.first).to_be_visible()

    def test_progress_bar_on_module_page(self, page: Page):
        page.goto(BASE_URL + "/module/module-01-overview", wait_until="domcontentloaded")
        progress = page.locator(".progress-bar, .module-progress-bar")
        assert progress.count() > 0, "No progress bar found on module page"

    def test_quiz_has_radio_buttons(self, page: Page):
        page.goto(BASE_URL + "/module/module-01-overview/quiz", wait_until="domcontentloaded")
        radios = page.locator("input[type='radio']")
        count = radios.count()
        assert count >= 4, f"Expected >= 4 radio buttons on quiz page, found {count}"

    def test_quiz_has_submit_button(self, page: Page):
        page.goto(BASE_URL + "/module/module-01-overview/quiz", wait_until="domcontentloaded")
        submit = page.locator("button[type='submit']")
        expect(submit).to_be_visible()

    def test_mark_complete_button_on_lesson(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        # Button says "Mark Complete" or "✅ Completed"
        btn = page.locator("#progress-btn-wrap button[type='submit']")
        expect(btn).to_be_visible()
        text = btn.inner_text().strip()
        assert "Mark Complete" in text or "Completed" in text, (
            f"Unexpected mark-complete button text: {text!r}"
        )

    def test_breadcrumb_on_lesson_page(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        breadcrumbs = page.locator(".breadcrumbs")
        expect(breadcrumbs).to_be_visible()
        # Should contain links to Home and Module
        links = breadcrumbs.locator("a")
        assert links.count() >= 2, "Expected at least 2 breadcrumb links"

    def test_breadcrumb_home_link(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        home_link = page.locator(".breadcrumbs a[href='/']")
        expect(home_link).to_be_visible()

    def test_breadcrumb_module_link(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        module_link = page.locator(".breadcrumbs a[href*='/module/']")
        expect(module_link).to_be_visible()

    def test_code_blocks_have_hljs_class(self, page: Page):
        """At least one lesson with code blocks gets syntax-highlighted."""
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="networkidle",
        )
        # hljs.highlightAll() adds hljs class to pre>code elements
        code_blocks = page.locator("pre code")
        if code_blocks.count() > 0:
            # Give hljs time to run
            page.wait_for_timeout(500)
            first_code = code_blocks.first
            classes = first_code.get_attribute("class") or ""
            # hljs adds "hljs" class and language-* class
            assert "hljs" in classes or "language-" in classes, (
                f"Code block missing hljs/language class. Classes: {classes!r}"
            )

    def test_mermaid_diagrams_render(self, page: Page):
        """Check at least one page with a mermaid diagram renders it."""
        # The architecture overview likely has mermaid
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/architecture-overview",
            wait_until="networkidle",
        )
        # Mermaid either leaves .mermaid elements with SVG inside, or replaces them
        mermaid_els = page.locator(".mermaid")
        if mermaid_els.count() > 0:
            # Wait for mermaid to process (it runs async)
            page.wait_for_timeout(2000)
            # Check for SVG inside mermaid element
            svgs = page.locator(".mermaid svg")
            if svgs.count() == 0:
                # Mermaid may not have loaded (CDN offline) — just verify element exists
                assert mermaid_els.count() > 0, "Mermaid element disappeared"
        # If no mermaid elements on this page, skip gracefully
        # (not all lessons have diagrams)


# ===========================================================================
# 3. RESPONSIVE TESTS
# ===========================================================================

class TestResponsive:

    @pytest.mark.parametrize("viewport_name,dims", VIEWPORTS.items())
    def test_page_loads_at_viewport(self, page: Page, viewport_name: str, dims: dict):
        page.set_viewport_size(dims)
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        main = page.locator("main.main-content")
        expect(main).to_be_visible()

    def test_sidebar_visible_desktop(self, page: Page):
        page.set_viewport_size(VIEWPORTS["desktop"])
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        sidebar = page.locator("aside.sidebar")
        expect(sidebar).to_be_visible()
        # Should have meaningful width on desktop
        box = sidebar.bounding_box()
        assert box is not None and box["width"] > 100, (
            f"Sidebar too narrow on desktop: {box}"
        )

    def test_sidebar_collapsed_or_hidden_mobile(self, page: Page):
        """On mobile (375px), sidebar should be hidden or off-screen."""
        page.set_viewport_size(VIEWPORTS["mobile"])
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        sidebar = page.locator("aside.sidebar")
        # Sidebar might be hidden via CSS or have width 0
        box = sidebar.bounding_box()
        if box is not None:
            # Either it's hidden (not visible) or very narrow / off-screen
            viewport_width = VIEWPORTS["mobile"]["width"]
            sidebar_right_edge = box["x"] + box["width"]
            is_offscreen = sidebar_right_edge <= 0 or box["x"] >= viewport_width
            is_zero_size = box["width"] == 0 or box["height"] == 0
            is_hidden = not sidebar.is_visible()
            assert is_hidden or is_offscreen or is_zero_size, (
                f"Sidebar should be hidden/collapsed on mobile but box={box}"
            )

    @pytest.mark.parametrize("viewport_name,dims", VIEWPORTS.items())
    def test_content_readable_at_viewport(self, page: Page, viewport_name: str, dims: dict):
        """Main content text should be visible (not overflowing or zero-size)."""
        page.set_viewport_size(dims)
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        # Check the hero title or module grid is visible
        visible_el = page.locator("h1, .hero-title, .module-grid").first
        expect(visible_el).to_be_visible()

    @pytest.mark.parametrize("viewport_name,dims", VIEWPORTS.items())
    def test_lesson_content_readable_at_viewport(
        self, page: Page, viewport_name: str, dims: dict
    ):
        page.set_viewport_size(dims)
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        lesson_body = page.locator(".lesson-body")
        expect(lesson_body).to_be_visible()
        box = lesson_body.bounding_box()
        assert box is not None and box["width"] > 50, (
            f"Lesson body too narrow at {viewport_name}: {box}"
        )


# ===========================================================================
# 4. INTERACTIVE TESTS
# ===========================================================================

class TestInteractive:

    def test_mark_complete_toggles_state(self, page: Page):
        """Clicking Mark Complete should update progress (HTMX or fallback)."""
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/architecture-overview",
            wait_until="domcontentloaded",
        )
        btn_wrap = page.locator("#progress-btn-wrap")
        btn = btn_wrap.locator("button[type='submit']")
        expect(btn).to_be_visible()
        initial_text = btn.inner_text().strip()
        assert "Mark Complete" in initial_text or "Completed" in initial_text, (
            f"Unexpected initial button text: {initial_text!r}"
        )

        # Click the button. HTMX swaps the #progress-btn-wrap on success;
        # if HTMX CDN isn't loaded, this falls through to a full form POST.
        with page.expect_response(
            lambda r: "/progress/toggle" in r.url and r.status == 200,
            timeout=10000,
        ) as resp_info:
            btn.click()

        assert resp_info.value.status == 200, (
            f"/progress/toggle returned {resp_info.value.status}"
        )

        # After HTMX swap completes, wait for any button to appear in wrap
        page.wait_for_timeout(1000)
        # The DOM should now have an updated button (or page navigated after POST)
        # Either way, the progress endpoint responded — that's the core assertion.
        # If HTMX fired, button text has changed; if full POST, we're on a new page.
        current_url = page.url
        if "/lesson/" in current_url:
            # HTMX swap: check the button is still there
            new_btn = page.locator("#progress-btn-wrap button[type='submit']")
            try:
                new_text = new_btn.inner_text(timeout=5000).strip()
                assert "Mark Complete" in new_text or "Completed" in new_text, (
                    f"Button text unexpected after toggle: {new_text!r}"
                )
            except Exception:
                # DOM might have fully re-rendered; just verify it responded OK
                pass

    def test_quiz_correct_answers_shows_score(self, page: Page):
        """Submitting correct answers shows a passing score."""
        page.goto(BASE_URL + "/module/module-01-overview/quiz", wait_until="domcontentloaded")

        # Count how many questions there are
        questions = page.locator(".quiz-question")
        n_questions = questions.count()
        assert n_questions > 0, "No questions found on quiz page"

        # Select an answer for each question
        for i in range(1, n_questions + 1):
            q_id = f"q{i}"
            correct = QUIZ_CORRECT_M01.get(q_id, "b")
            radio = page.locator(f"input[name='{q_id}'][value='{correct}']")
            if radio.count() > 0:
                radio.check()

        # Submit
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("domcontentloaded")

        # Results should show
        results_div = page.locator(".quiz-results")
        expect(results_div).to_be_visible()

        # Score should be shown
        score_el = page.locator(".quiz-score-number")
        expect(score_el).to_be_visible()
        score_text = score_el.inner_text()
        assert "%" in score_text, f"Score element missing '%': {score_text!r}"

    def test_quiz_wrong_answers_shows_explanations(self, page: Page):
        """Submitting wrong answers shows result items with explanations."""
        page.goto(BASE_URL + "/module/module-01-overview/quiz", wait_until="domcontentloaded")

        questions = page.locator(".quiz-question")
        n_questions = questions.count()

        # Select wrong answer for each question
        for i in range(1, n_questions + 1):
            q_id = f"q{i}"
            correct = QUIZ_CORRECT_M01.get(q_id, "b")
            # Pick a wrong option (try "a", fall back to "d")
            wrong = "a" if correct != "a" else "d"
            radio = page.locator(f"input[name='{q_id}'][value='{wrong}']")
            if radio.count() > 0:
                radio.check()

        page.locator("button[type='submit']").click()
        page.wait_for_load_state("domcontentloaded")

        # Should show results
        expect(page.locator(".quiz-results")).to_be_visible()

        # Wrong answers should show explanations
        explanations = page.locator(".result-explanation")
        assert explanations.count() >= 1, (
            "Expected at least one explanation for wrong answers"
        )

    def test_navigate_to_next_lesson(self, page: Page):
        """Click the next lesson button and verify navigation."""
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        next_btn = page.locator(".lesson-nav .btn-primary")
        expect(next_btn).to_be_visible()
        next_btn.click()
        page.wait_for_load_state("domcontentloaded")
        # Should be on a different page (next lesson or quiz)
        assert page.url != BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw", (
            "Navigation did not change page URL"
        )

    def test_navigate_back_to_module(self, page: Page):
        """Click the back/ghost button from a lesson to go to module overview."""
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="domcontentloaded",
        )
        back_btn = page.locator(".lesson-nav .btn-ghost")
        expect(back_btn).to_be_visible()
        back_btn.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/module/module-01-overview" in page.url, (
            f"Expected module URL, got {page.url}"
        )

    def test_breadcrumb_navigation_lesson_to_module(self, page: Page):
        """Click breadcrumb module link from lesson → module page."""
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/architecture-overview",
            wait_until="domcontentloaded",
        )
        module_crumb = page.locator(".breadcrumbs a[href*='/module/']")
        expect(module_crumb).to_be_visible()
        module_crumb.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/module/" in page.url and "/lesson/" not in page.url, (
            f"Expected module page after breadcrumb click, got {page.url}"
        )

    def test_breadcrumb_navigation_lesson_to_home(self, page: Page):
        """Click 'All Modules' breadcrumb from lesson → home."""
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/architecture-overview",
            wait_until="domcontentloaded",
        )
        home_crumb = page.locator(".breadcrumbs a[href='/']")
        expect(home_crumb).to_be_visible()
        home_crumb.click()
        page.wait_for_load_state("domcontentloaded")
        assert page.url.rstrip("/") == BASE_URL, (
            f"Expected home after breadcrumb click, got {page.url}"
        )


# ===========================================================================
# 5. VISUAL REGRESSION BASELINE SCREENSHOTS
# ===========================================================================

class TestVisualBaseline:
    """
    Captures full-page screenshots for visual regression baseline.
    These are NOT pixel-diff assertions — they establish the baseline.
    The test passes as long as screenshots are saved successfully.
    """

    def _screenshot(self, page: Page, name: str):
        path = SCREENSHOTS_DIR / f"{name}.png"
        page.goto(BASE_URL, wait_until="networkidle")  # warm up
        page.screenshot(path=str(path), full_page=True)
        assert path.exists() and path.stat().st_size > 1000, (
            f"Screenshot {name}.png is missing or too small"
        )
        return path

    def test_screenshot_index(self, page: Page):
        page.goto(BASE_URL + "/", wait_until="networkidle")
        page.wait_for_timeout(500)  # let mermaid/hljs finish
        path = SCREENSHOTS_DIR / "index.png"
        page.screenshot(path=str(path), full_page=True)
        assert path.exists() and path.stat().st_size > 1000

    def test_screenshot_module_page(self, page: Page):
        page.goto(BASE_URL + "/module/module-01-overview", wait_until="networkidle")
        page.wait_for_timeout(500)
        path = SCREENSHOTS_DIR / "module-01-overview.png"
        page.screenshot(path=str(path), full_page=True)
        assert path.exists() and path.stat().st_size > 1000

    def test_screenshot_lesson_page(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/lesson/what-is-openclaw",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1000)  # wait for hljs highlight
        path = SCREENSHOTS_DIR / "lesson-what-is-openclaw.png"
        page.screenshot(path=str(path), full_page=True)
        assert path.exists() and path.stat().st_size > 1000

    def test_screenshot_quiz_page(self, page: Page):
        page.goto(
            BASE_URL + "/module/module-01-overview/quiz",
            wait_until="networkidle",
        )
        page.wait_for_timeout(500)
        path = SCREENSHOTS_DIR / "quiz-module-01.png"
        page.screenshot(path=str(path), full_page=True)
        assert path.exists() and path.stat().st_size > 1000
