import readline
import sys
import subprocess
import signal
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import json
from pathlib import Path
import random


import re

pattern = r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$"

mode = "input"
next_id = 0
executor = ThreadPoolExecutor()

DEFAULTFILE = "./timers.json"
Path(DEFAULTFILE).touch()
timers_data = {}

sisyphus_count = 0

# Reset
RESET = "\033[0m"

# Regular colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
YELLOW = "\033[33m"

# Styles
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"


class Timer:
    def __init__(self, start, end, n, name=None):
        self.end = end
        self.start = start
        self.ended = False
        self.id = n
        self.cancelled = Event()
        self.timer_cancelled = False
        self.name = name or f"Timer #{self.id}"
        self.timer_started()

    def timer_started(self):
        if self.timer_cancelled:
            return
        seconds_to_wait = (self.end - datetime.now()).total_seconds()
        seconds_to_wait = max(0, seconds_to_wait)
        future = executor.submit(self.task, seconds_to_wait)
        future.add_done_callback(self.timer_ended)

    def notify(self):
        duration = int((self.end - self.start).total_seconds())

        subprocess.run(
            [
                "notify-send",
                f"{self.name}",
                f"Finished\nDuration: {timedelta(seconds=duration)}",
                "-u",
                "normal",
                "-t",
                "5000",
            ]
        )

        subprocess.run(
            [
                "spd-say",
                f"Timer {self.name} finished. "
                f"Duration {duration // 60} minutes {duration % 60} seconds.",
            ]
        )

    def timer_ended(self, future):
        try:
            completed = future.result()
            if completed:
                self.ended = True
                self.notify()

            else:
                self.timer_cancelled = True
                return

        except Exception as e:
            return

    def task(self, seconds_to_wait):
        return not self.cancelled.wait(seconds_to_wait)

    def die(self):
        self.cancelled.set()

    def __repr__(self):
        if self.ended:
            r = f"{GREEN}{UNDERLINE}ENDED{RESET} at {WHITE}{BOLD}{self.end.strftime('%I:%M:%S %p')}{RESET}!"
        elif self.timer_cancelled:
            r = f"{RED}{BOLD}GOT CANCELLED{RESET}"
        else:
            total_duration = (self.end - self.start).total_seconds()
            duration = timedelta(seconds=int(total_duration))
            now = datetime.now()
            remaining = max(0, int((self.end - now).total_seconds()))
            remaining_str = str(timedelta(seconds=remaining))
            if total_duration <= 0:
                pct = 100.0
            else:
                elapsed = (now - self.start).total_seconds()
                pct = (elapsed / total_duration) * 100
                pct = min(100.0, max(0.0, pct))

            r = f"remaining: {GREEN}{BOLD}{UNDERLINE}{remaining_str}{RESET} | {MAGENTA}{BOLD}{UNDERLINE}{duration}{RESET} | {now.strftime('%I:%M:%S %p')} // {self.end.strftime('%I:%M:%S %p')} | {CYAN}{pct:.1f}%{RESET}"

        return r


def set_timer(timers, h, m, s):
    """
    Sets a new timer with hours, minutes, seconds as arguments
    """
    global next_id
    h, m, s = int(h), int(m), int(s)
    now = datetime.now()
    end_time = now + timedelta(hours=h, minutes=m, seconds=s)
    next_id += 1
    timer = Timer(end=end_time, start=now, n=next_id)
    timers[timer.id] = timer
    return f"{GREEN}Made a new timer ending at {end_time.strftime('%I:%M:%S %p')} :){RESET}"


def named_timer(timers, name, timestr):
    """
    Create a timer with a name and a ease-of-use format for time (XhYmZs)
    """
    global timers_data
    matched = re.fullmatch(pattern, timestr)

    if not matched:
        return f"{RED}Invalid duration given{RESET}: {timestr}"

    h = int(matched.group(1) or 0)
    m = int(matched.group(2) or 0)
    s = int(matched.group(3) or 0)

    timers_data[name] = h, m, s

    return f"{GREEN}Made a named timer {name}, that will time for {h} hours {m} minutes {s} seconds :){RESET}"


def start_timer(timers, name):
    """
    Start a named timer with a name
    """
    if name not in timers_data:
        return f"{RED}Timer with name{RESET} {WHITE}{UNDERLINE}{name}{RESET} {RED}not found{RESET}"

    global next_id
    now = datetime.now()
    h, m, s = timers_data[name]
    end_time = now + timedelta(hours=h, minutes=m, seconds=s)
    next_id += 1
    timer = Timer(end=end_time, start=now, n=next_id, name=name)
    timers[timer.id] = timer

    return f"{GREEN}Timer with name{RESET} {WHITE}{UNDERLINE}{name}{RESET} {GREEN}started with id #{next_id}{RESET}"


def stop_timer(timers, inp):
    """
    Stop a named timer with a name or id
    """
    if not inp.isdigit():
        if inp not in timers_data:
            return f"{RED}Timer with name{RESET} {WHITE}{UNDERLINE}{inp}{RESET} {RED}not found{RESET}"

        ids = []
        for timer in timers.values():
            if timer.name == inp and not timer.timer_cancelled and not timer.ended:
                ids.append(timer.id)
        return f"{GREEN}Timer, with name{RESET} {WHITE}{UNDERLINE}{inp}{RESET} {GREEN}has multiple IDs: {RESET} {WHITE}{UNDERLINE}{ids}{RESET}"

    else:
        if int(inp) not in timers:
            return f"{RED}Timer with id {RESET}{WHITE}{UNDERLINE}{inp}{RESET} {RED}not found{RESET}"
        timer = timers[int(inp)]
        if timer.timer_cancelled or timer.ended:
            return f"{RED}Timer with id {RESET}{WHITE}{UNDERLINE}{inp}{RESET} {RED}is not running{RESET}"
        timer.die()
        return f"{GREEN}Timer, with id {RESET}{WHITE}{UNDERLINE}{inp}{RESET} {GREEN}is stopped successfully.{RESET}"


def save_timers(timers):
    """
    Save all timers to the default file
    """
    try:
        with open(DEFAULTFILE, "w") as fl:
            json.dump(timers_data, fl)
        return f"{GREEN}Timers are written to {DEFAULTFILE} successfully :){RESET}"
    except Exception as e:
        return f"{RED}Exception: {str(e)} has occurred and couldn't save them :({RESET}"


def clear_timer(timers, n):
    """
    Removes a timer identified by index as argument
    """
    n = int(n)

    if n not in timers:
        return f"{RED}Timer #{n} does not exist{RESET}"

    timers[n].die()
    del timers[n]

    return f"{GREEN}Removed timer #{n}{RESET}"


def random_quote(timers):
    """
    Gives you a very important quote back
    """
    quote_bag = [
        "A scientist is someone who knows more and more about less and less, until he knows everything about nothing. — Konrad Lorenz",
        "The creation of unpredictable numbers is considered too critical to be left to chance. — Robert Covey",
        "Human beings want to be good, but not too good, and not quite all the time. — George Orwell",
        "Reality is a collective hunch. — Lily Tomlin",
        "There is no doubt that Hegel's philosophy was obscure; the only question is whether it was profound. — Bertrand Russell",
        "If a man can remain calm amidst all this chaos, he simply doesn't have all the facts. — Anonymous",
        "We live in an age when unnecessary things are our only necessities. — Oscar Wilde",
        "Is man merely a mistake of God's? Or God merely a mistake of man? — Friedrich Nietzsche",
        "When I accept myself just as I am, then I can change. — Carl Rogers",
        "People who carry notepads to the bedroom or scribble down thoughts during morning constitutionals have tools to abandon self-delusions. Or develop them. — Nolan Yuma",
    ]
    return f'Here is a quote: "{WHITE}{UNDERLINE}{BOLD}{random.choice(quote_bag)}{RESET}" :P'


def sisyphus_update(timers):
    """
    Simulates the human condition.
    Run repeatedly to advance the Sisyphus count.
    Wait for the running sisyphus timer to finish, to increase the count.
    Running it too early i.e. before the timer completes, resets all progress/sispyphus count.
    """
    global sisyphus_count

    runnings = []
    ended = []

    # CANCELLED
    # ENDED
    # RUNNING

    for timer in timers.values():
        if timer.name == "sisyphus" and not timer.timer_cancelled:
            if timer.ended:
                ended.append(timer)
            else:
                runnings.append(timer)

    if len(runnings) == 0 and len(ended) == 0:
        start_timer(timers, "sisyphus")
        return (
            f"{CYAN}{BOLD}The boulder begins its journey.{RESET} "
            f"(count: {WHITE}{UNDERLINE}{sisyphus_count}{RESET})"
        )

    if len(runnings) == 0 and len(ended) >= 1:
        sisyphus_count += 1
        start_timer(timers, "sisyphus")
        return (
            f"{GREEN}{BOLD}The boulder rolls again.{RESET} "
            f"Sisyphus count increased to "
            f"{WHITE}{UNDERLINE}{sisyphus_count}{RESET}."
        )
    elif len(runnings) >= 1:
        for running in runnings:
            running.die()
        sisyphus_count = 0

        return (
            f"{RED}{BOLD}You pushed too soon. The gods are displeased. Giving up? OR Live absurdly again?{RESET} "
            f"Sisyphus count reset to "
            f"{WHITE}{UNDERLINE}{sisyphus_count}{RESET}."
        )


def help(timers):
    """
    Provides command help for usage
    """
    buff = []
    buff.append("\n==============\n")
    buff.append("Use Ctrl+Z to switch modes\n")
    buff.append("==============\n")
    buff.append("\n\t==============")
    for command, data in ops.items():
        f, nargs = data
        buff.append(
            f"\t\n{UNDERLINE}Name{RESET}: {command}\n\t{UNDERLINE}Takes #{nargs} argument(s){RESET}\n\t{UNDERLINE}Docstring{RESET}: {f.__doc__}"
        )
        buff.append("\n\t==============")
    return "".join(buff)


def exit(timers):
    """
    Exits the program
    """
    for timer in timers.values():
        timer.die()
    executor.shutdown(wait=False)
    sys.exit(0)


ops = {
    "set": (set_timer, 3),
    "clear": (clear_timer, 1),
    "help": (help, 0),
    "exit": (exit, 0),
    "timer": (named_timer, 2),
    "start": (start_timer, 1),
    "stop": (stop_timer, 1),
    "save": (save_timers, 0),
    "quote": (random_quote, 0),
    "sisyphus": (sisyphus_update, 0),
}


# def init_screen():
#     print("\033[s", end="")  # save cursor position


# def clear_screen():
#     print("\033[u\033[J", end="")  # restore cursor + clear to end of screen


def clear_screen():
    print("\033[2J\033[H", end="")


def execute_command(cmd, timers):
    words = cmd.rstrip().split(" ")
    main, args = words[0], words[1:]
    if main not in ops:
        return f"{RED}Unknown command: {main}{RESET}", False
    func, n = ops[main]
    if len(args) != n:
        return (
            f"{RED}Argument length mismatch, needed {n}, got {len(args)}{RESET}",
            False,
        )
    resp = func(timers, *args)
    return resp, True


def print_history(history):
    # for i, response in enumerate(history):
    # lets only print the last command
    i = len(history)
    if i == 0:
        return
    response = history[-1]
    cmd, resp = response
    message, success = resp
    print("+++++++")
    print(
        f"#{i}\nexecuted: {cmd}\nsuccess: {success}\nmessage: \n___\n{message}\n___\n"
    )
    print("-------")


def handle_input(timers, cmd_history):
    while True:
        clear_screen()
        print_history(cmd_history)
        cmd = input(f"{CYAN}{ITALIC}mode{RESET}: {mode} > ")
        resp, success = execute_command(cmd, timers)
        cmd_history.append((cmd, (resp, success)))


def print_info(timers):
    while True:
        clear_screen()
        print(f"{CYAN}{ITALIC}mode{RESET}: {mode}")
        print(
            f"{YELLOW}{BOLD}Sisyphus Count:{RESET} "
            f"{YELLOW}{UNDERLINE}{sisyphus_count}{RESET}"
        )
        print(f"{WHITE}{DIM}TIME NOW - {datetime.now().strftime('%I:%M:%S %p')}{RESET}")
        for timer_id, timer in timers.items():
            print(
                f"{MAGENTA}{UNDERLINE}ID: #{timer.id}{RESET} {WHITE}{BOLD}{timer.name} -{RESET}",
                timer,
            )
        print("---------")
        for name, time_data in timers_data.items():
            h, m, s = time_data
            print(f"{WHITE}{BOLD}{name} -{RESET} {WHITE}{UNDERLINE}{h}h{m}m{s}s{RESET}")
        time.sleep(2)


def handle_ctrl_z(signum, frame):
    global mode
    if mode == "timers":
        mode = "input"
    else:
        mode = "timers"

    raise InterruptedError


def load_timers():
    try:
        global timers_data
        with open(DEFAULTFILE) as fl:
            timers_data = json.load(fl)
        if "sisyphus" not in timers_data:
            timers_data["sisyphus"] = [0, 1, 0]
    except:
        return


def main():
    timers = {}

    signal.signal(signal.SIGTSTP, handle_ctrl_z)

    load_timers()

    # init_screen()
    clear_screen()

    cmd_history = []

    while True:
        try:
            if mode == "input":
                handle_input(timers, cmd_history)
                continue

            if mode == "timers":
                print_info(timers)
                continue

        except InterruptedError:
            clear_screen()

        except KeyboardInterrupt:
            exit(timers)
            print("\nbye.")
            break


main()
