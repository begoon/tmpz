from typing import Any, Generator

import pytest
from pytest import Item, TestReport


def hook_name(name: str, **kwarg: Any) -> str:
    args = " | ".join(f"{name}={v!r}" for name, v in kwarg.items())
    result = "\n\n" + WHITE + f"HOOK {name}" + RC
    if args:
        result += "\n" + GRAY + "---- " + args + RC
    return result


@pytest.hookimpl(wrapper=True)
def pytest_collection_modifyitems(
    config,
    items: list[Item],
) -> Generator[None, None]:
    print(hook_name("pytest_collection_modifyitems", items=len(items)))
    for index, item in enumerate(items, start=1):
        print(index, item.name, item.nodeid, item.fspath)
    yield


def pytest_collection_finish(session: pytest.Session) -> None:
    print(hook_name("pytest_collection_finish", items=len(session.items)))


def pytest_runtest_logstart(nodeid: str, location: tuple) -> None:
    print(
        hook_name(
            "pytest_runtest_logstart",
            nodeid=nodeid,
            location=location,
        )
    )


def pytest_runtest_logfinish(nodeid: str, location: tuple) -> None:
    print(
        hook_name(
            "pytest_runtest_logfinish",
            nodeid=nodeid,
            location=location,
        )
    )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: Item) -> Generator[None, None]:
    print(hook_name("pytest_runtest_call", item=item.name))

    print(GRAY + "pytest_runtest_call: BEFORE" + RC, item.name)

    yield

    print(GRAY + "pytest_runtest_call: AFTER" + RC)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: Item,
    call: pytest.CallInfo,
) -> Generator[None, None]:
    report = yield
    hook_name(
        "pytest_runtest_makereport",
        item=item.name,
        call=call,
        report=report,
        duration=f"{call.duration:.4f}s",
    )
    return report


@pytest.hookspec(firstresult=True)
@pytest.hookimpl(wrapper=True)
def pytest_report_teststatus(
    report: TestReport,
    config: pytest.Config,
) -> Generator[None, None]:
    print(hook_name("pytest_report_teststatus", report=report))
    if report.when != "call":
        result = yield
        return result
    yield
    match report.outcome:
        case "skipped":
            return (report.outcome, "s", YELLOW_BACKGROUND + "SKIP" + RC)
        case "failed":
            return (report.outcome, "F", "FAIL")
        case "passed":
            return (report.outcome, "*", YELLOW + "PASS" + RC)
    assert False, f"unhandled outcome: {report.outcome}"


YELLOW_BACKGROUND = "\033[43m"

WHITE = "\033[97m"
RED = "\033[91m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GRAY = "\033[90m"

RC = "\033[0m"


@pytest.hookimpl(wrapper=True)
def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
) -> Generator[None, None]:
    terminalreporter.write_sep(
        "-",
        "terminal summary from conftest.py",
        Blue=True,
    )
    session = terminalreporter._session
    for i, item in enumerate(session.items, start=1):
        terminalreporter.write_line(f"test: {i}: {item.name}")

    terminalreporter.write_line(f"exit status: {exitstatus}")

    yield
