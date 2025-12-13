import subprocess
import time
import os
from behave import fixture, use_fixture
from playwright.sync_api import sync_playwright


@fixture
def start_blackboard_app(context):
    # Start the Flet app in web mode
    # We use a specific port to ensure we know where to connect
    port = 8550
    context.base_url = f"http://localhost:{port}"

    # Command to run the app
    cmd = ["uv", "run", "flet", "run", "--web", "--port", str(port), "src/main.py"]

    # Start the process
    kwargs = {}
    if os.name == "posix":
        kwargs["preexec_fn"] = os.setsid
    elif os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    context.app_process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
    )

    # Wait a bit for the server to start
    time.sleep(10)

    yield context.app_process

    # Teardown
    if os.name == "posix":
        os.killpg(os.getpgid(context.app_process.pid), 15)  # SIGTERM
    else:
        # On Windows, kill the process tree
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(context.app_process.pid)])

    context.app_process.wait()


@fixture
def browser_context(context):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context.page = browser.new_page()
        yield context.page
        browser.close()


def before_all(context):
    use_fixture(start_blackboard_app, context)


def before_scenario(context, scenario):
    use_fixture(browser_context, context)
