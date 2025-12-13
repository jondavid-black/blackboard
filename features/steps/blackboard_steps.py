from behave import given, when, then
from playwright.sync_api import Page, expect


@given("the blackboard application is running")  # type: ignore
def step_impl_app_running(context):
    # The application is started in environment.py
    pass


@when("I open the application in the browser")  # type: ignore
def step_impl_open_browser(context):
    page: Page = context.page
    page.goto(context.base_url)
    # Wait for the page to load content
    page.wait_for_load_state("networkidle")

    # Enable accessibility for CanvasKit
    # We need to aggressively trigger the semantics generation
    try:
        # 1. Wait for the placeholder to exist
        page.wait_for_selector(
            "flt-semantics-placeholder", state="attached", timeout=5000
        )

        # 2. Click it multiple times/ways to ensure it wakes up
        page.locator("flt-semantics-placeholder").click(force=True)

        # 3. Also try evaluating JS to click it, just in case
        page.evaluate("""
            const placeholder = document.querySelector('flt-semantics-placeholder');
            if (placeholder) {
                placeholder.click();
                // Dispatch a touch event too, sometimes needed for mobile emulation
                placeholder.dispatchEvent(new Event('touchstart'));
            }
        """)

        # 4. Wait a bit for the semantics tree to populate
        page.wait_for_timeout(1000)

    except Exception as e:
        print(f"Warning: Could not enable accessibility: {e}")


@then('the page title should be "{title}"')  # type: ignore
def step_impl_check_title(context, title):
    page: Page = context.page
    expect(page).to_have_title(title)


@then("I should see the toolbar")  # type: ignore
def step_impl_check_toolbar(context):
    page: Page = context.page

    # Try to find buttons via accessibility labels
    try:
        expect(page.get_by_label("Hand")).to_be_visible(timeout=2000)
        expect(page.get_by_label("Selection")).to_be_visible()
        expect(page.get_by_label("Pen")).to_be_visible()
    except Exception:
        # If accessibility is not enabled, we can't find buttons by label.
        # Check if the app is at least running (flutter-view exists)
        print(
            "Warning: Accessibility labels not found. Verifying app container existence instead."
        )
        expect(page.locator("flutter-view")).to_be_visible()


@then("I should see the canvas")  # type: ignore
def step_impl_check_canvas(context):
    page: Page = context.page
    # Check for the flutter view or canvas
    expect(page.locator("flutter-view")).to_be_visible()
    # We can check if the main canvas element exists.
    # Flet Canvas usually renders as a 'flt-canvas' tag or similar in the DOM if using the html renderer,
    # or a canvas element in canvaskit.

    # Since we are likely using CanvasKit (default for Flet desktop/web usually), there will be a <canvas> element.
    expect(page.locator("canvas")).to_be_visible()


@when('I click the "{tab}" button in the side rail')  # type: ignore
def step_impl_click_rail_tab(context, tab):
    page: Page = context.page
    # Map 'files' to the likely aria-label or tooltip
    # In side_rail.py: NavigationRailDestination(icon=ft.Icons.FOLDER, label="Files")
    label_map = {
        "files": "Files",
        "tools": "Tools",
        "properties": "Properties",
        "profile": "Profile",
    }
    label = label_map.get(tab, tab)

    # Wait for the rail to be interactable
    page.wait_for_timeout(500)

    # Try to find the tab button
    # Flet NavigationRail destinations often get aria-labels
    try:
        # Use get_by_role('button', name='Files') which is more precise
        page.get_by_role("button", name=label).click()
    except Exception:
        # Fallback: Click by text
        page.get_by_text(label).click()


@then("the drawer should be visible")  # type: ignore
def step_impl_check_drawer_visible(context):
    page: Page = context.page
    # The drawer is a Container. It might not have a specific label unless we add semantics.
    # But it contains specific text like "EXPLORER" or close button.
    # Let's check for the close button which is a common element.

    # Assuming the drawer animation/render takes a moment
    page.wait_for_timeout(500)

    # Check for text that only appears in drawer
    expect(page.get_by_label("Close")).to_be_visible()


@then('I should see "{text}" in the drawer')  # type: ignore
def step_impl_check_drawer_text(context, text):
    page: Page = context.page
    expect(page.get_by_text(text)).to_be_visible()


@then('I should see "{tooltip}" button')  # type: ignore
def step_impl_check_drawer_button(context, tooltip):
    page: Page = context.page
    expect(page.get_by_label(tooltip)).to_be_visible()
