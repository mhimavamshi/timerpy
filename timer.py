import readline
from datetime import datetime, timedelta
import time 

class Timer:
    def __init__(self, end, n):
        self.end = end
        self.curr = 0
        self.id = n

    def start(self):
        # needs to run concurrently - threads or others
        pass

    def __repr__(self):
        return f"{self.curr} // {self.end}" # dynamically calculate progress bar

def set_timer(timers, h, m, s):
    h, m, s = int(h), int(m), int(s)
    end_time = datetime.now() + timedelta(hours=h, minutes=m, seconds=s)
    timer = Timer(end=end_time, n=len(timers)+1)
    timers[timer.id] = timer

ops = {
    "set": (set_timer, 3)
}

def clear_screen():
    print("\033[2J\033[H", end="")

def get_command():
    return input("> ")

def execute_command(cmd, timers):
    words = cmd.split(" ")
    main, args = words[0], words[1:]
    if main not in ops:
        return 
    func, n = ops[main]
    if len(args) != n:
        return
    func(timers, *args)


def main():
    timers = {}

    while True:
        clear_screen()
        for timer_id, timer in timers.items():
            print(f"Timer #{timer_id} -", timer)
        cmd = get_command()
        execute_command(cmd, timers)

main()