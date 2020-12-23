"""Run using:
celery -A hkis worker
"""

import asyncio
from functools import partial
from random import choice
import os
import tempfile
from subprocess import Popen, PIPE, run, STDOUT, TimeoutExpired, DEVNULL

from logging import getLogger

from celery import shared_task


logger = getLogger(__name__)

FIREJAIL_OPTIONS = [
    "--quiet",
    "--net=none",
    "--shell=none",
    "--x11=none",
    "--protocol=inet",
    "--private-dev",
    "--private-bin=python3",
    "--private-etc=group,hostname,localtime,nsswitch.conf,passwd,resolv.conf,alternatives",
    "--private-tmp",
    "--caps.drop=all",
    "--noprofile",
    "--nonewprivs",
    "--nosound",
    "--no3d",
    "--nogroups",
    "--noroot",
    "--seccomp",
    "--rlimit-fsize=8192",
    "--rlimit-nofile=100",
    "--rlimit-nproc=2000",
    "--rlimit-cpu=20",
    "--blacklist=/var",
    "--blacklist=/sys",
    "--blacklist=/boot",
]


@shared_task
def run_snippet_task(source_code: str) -> str:
    with tempfile.TemporaryDirectory(prefix="hkis_snippets") as tmpdir:
        with open(os.path.join(tmpdir, "snippet.py"), "w") as snippet_file:
            snippet_file.write(source_code)
        firejail_env = os.environ.copy()
        prof_proc = Popen(
            ["firejail"]
            + FIREJAIL_OPTIONS
            + ["--private=" + tmpdir, "python3", os.path.expanduser("~/snippet.py")],
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=STDOUT,
            cwd=os.path.expanduser("~/"),
            env=firejail_env,
        )
        try:
            stdout = prof_proc.communicate(timeout=40)[0]
            if prof_proc.returncode == 255:
                return "Checker timed out, look for infinite loops maybe?"
            return stdout.decode("UTF-8", "backslashreplace").replace(
                "\u0000", r"\x00"
            )[:65_536]
        except TimeoutExpired:
            prof_proc.kill()
            prof_proc.wait()
            return "Timed out after 20 seconds."


def congrats(language):
    """Generates a congratulation sentence."""
    return (
        choice(
            {
                "en": [
                    "Congrats",
                    "Nice job",
                    "Well done",
                    "Spot on",
                    "Bravo",
                    "Nice",
                    "Good",
                ],
                "fr": [
                    "Bravo",
                    "Bien joué",
                    "Super",
                    "Excellent",
                    "Joli",
                ],
            }[language]
        )
        + choice(
            {
                "en": ["! ", "!! ", "!!! ", "! ! "],
                "fr": [" ! ", " !! ", " !!! ", " ! ! "],
            }[language]
        )
        + choice(
            {
                "en": [
                    "Your exercise is OK.",
                    "Right answer.",
                    "Good answer.",
                    "Correct answer.",
                    "Looks good to me!",
                    "Your answer is right.",
                    "Your answer is correct.",
                ],
                "fr": [
                    "C'est juste.",
                    "Bonne réponse.",
                    "Correct.",
                    "Ça me semble bon.",
                    "C'est la bonne réponse.",
                    "Excellente réponse.",
                ],
            }[language]
        )
    )


@shared_task
def check_answer_task(answer: dict):
    """Executed on Celery workers.
    answer should contain: check, source_code, and language.
    """
    with tempfile.TemporaryDirectory(prefix="hkis") as tmpdir:
        with open(os.path.join(tmpdir, "check.py"), "w") as check_file:
            check_file.write(answer["check"])
        with open(os.path.join(tmpdir, "solution.py"), "w") as answer_file:
            answer_file.write(answer["source_code"])
        firejail_env = os.environ.copy()
        if "language" in answer:
            firejail_env["LANGUAGE"] = answer["language"]
        if "pre_check" in answer and answer["pre_check"]:
            # Run a pre-check script outside the sandbox before the actual check.
            with open(os.path.join(tmpdir, "pre_check.py"), "w") as pre_check_file:
                pre_check_file.write(answer["pre_check"])
            logger.info("Running pre-check")
            pre_check_result = run(
                ["python3", os.path.join(tmpdir, "pre_check.py")],
                cwd=tmpdir,
                stdin=DEVNULL,
                stdout=PIPE,
                stderr=PIPE,
                env=firejail_env,
            )
            if pre_check_result.returncode != 0 or pre_check_result.stderr:
                logger.warning(
                    "pre_check failed with code %d, stdout: %s, stderr: %s",
                    pre_check_result.returncode,
                    pre_check_result.stdout,
                    pre_check_result.stderr,
                )
        prof_proc = Popen(
            ["firejail"]
            + FIREJAIL_OPTIONS
            + ["--private=" + tmpdir, "python3", os.path.expanduser("~/check.py")],
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=STDOUT,
            cwd=os.path.expanduser("~/"),
            env=firejail_env,
        )
        try:
            stdout = (
                prof_proc.communicate(timeout=40)[0]
                .decode("UTF-8", "backslashreplace")
                .replace("\u0000", r"\x00")
                .replace(  # Simplify tracebacks by hiding the temporary directory
                    'File "' + os.path.expanduser("~/"), 'File "'
                )
            )[:65_536]
            if prof_proc.returncode == 255:
                return False, "Checker timed out, look for infinite loops maybe?"
            if prof_proc.returncode != 0 or stdout:
                return False, stdout
            return True, congrats(answer.get("language", "en"))
        except TimeoutExpired:
            prof_proc.kill()
            prof_proc.wait()
            return False, "Checker timed out."


async def check_answer(answer: dict):
    """Executed Django side.

    TODO with Celery 5: should no longer need run_in_executor.
    """

    def sync_celery_check_answer(answer: dict):
        return check_answer_task.apply_async((answer,), expires=60).get()

    return await asyncio.get_running_loop().run_in_executor(
        None, partial(sync_celery_check_answer, answer=answer)
    )


async def run_snippet(source_code: str) -> str:
    """Executed Django side.

    TODO with Celery 5: should no longer need run_in_executor.
    """

    def sync_celery_check_answer(source_code: str):
        return run_snippet_task.apply_async((source_code,), expires=60).get()

    return await asyncio.get_running_loop().run_in_executor(
        None, partial(sync_celery_check_answer, source_code=source_code)
    )
