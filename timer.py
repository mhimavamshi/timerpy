import readline
import signal
from datetime import datetime, timedelta
import time 
from concurrent.futures import ThreadPoolExecutor

mode = "timers" 

executor = ThreadPoolExecutor()



class Timer:
    def __init__(self, start, end, n):
        self.end = end
        self.start = datetime.now()  
        self.ended = False
        self.id = n
        self.timer_started()

    def timer_started(self):
        seconds_to_wait = (self.end - datetime.now()).total_seconds()
        seconds_to_wait = max(0, seconds_to_wait)
        future = executor.submit(self.task, seconds_to_wait)
        future.add_done_callback(self.timer_ended)
        
    def timer_ended(self, future):
        try:
            _ = future.result()
            self.ended = True

            # here we can do notification or whatever you want!
            
        except Exception as e:
            return

    def task(self, seconds_to_wait):
        time.sleep(seconds_to_wait)
        return "ended :("

    def __repr__(self):
        if self.ended:
            r = f"ENDED at {self.end.strftime("%I:%M:%S %p")}!"
        else:
            total_duration = (self.end - self.start).total_seconds()
            now = datetime.now()
            if total_duration <= 0:
                pct = 100.0
            else:
                elapsed = (now - self.start).total_seconds()
                pct = (elapsed / total_duration) * 100
                pct = min(100.0, max(0.0, pct))  # Clamp between 0% and 100%

            r = f"{now.strftime("%I:%M:%S %p")} // {self.end.strftime("%I:%M:%S %p")} | {pct:.1f}%"
        
        return r

def set_timer(timers, h, m, s):
    h, m, s = int(h), int(m), int(s)
    now = datetime.now()
    end_time = now + timedelta(hours=h, minutes=m, seconds=s)
    timer = Timer(end=end_time, start=now, n=len(timers)+1)
    timers[timer.id] = timer
    return f"Made a new timer ending at {end_time.strftime("%I:%M:%S %p")} :)"

ops = {
    "set": (set_timer, 3)
}

def clear_screen():
    print("\033[2J\033[H", end="")


def execute_command(cmd, timers):
    words = cmd.split(" ")
    main, args = words[0], words[1:]
    if main not in ops:
        return "failed", False
    func, n = ops[main]
    if len(args) != n:
        return "failed", False
    resp = func(timers, *args)
    return resp, True

def print_history(history):
    for i, response in enumerate(history):
        cmd, resp = response
        message, success = resp 
        print("=====")
        print(f"#{i+1}\nexecuted: {cmd}\nsuccess: {success}\nmessage: {message}")
        print("=====")

def handle_input(timers, cmd_history):
    while True:
        clear_screen()
        print_history(cmd_history)
        cmd = input(f"mode: {mode} > ")
        resp, success = execute_command(cmd, timers)
        cmd_history.append((cmd, (resp, success)))

def print_info(timers):
    while True:
        clear_screen()
        print(f"mode: {mode}")
        print(f"TIME NOW - {datetime.now().strftime("%I:%M:%S %p")}")
        for timer_id, timer in timers.items():
            print(f"Timer #{timer_id} -", timer)
        time.sleep(1)

def handle_ctrl_z(signum, frame):
    global mode
    if mode == "timers":
        mode = "input"
    else:
        mode = "timers"
    
    raise InterruptedError

def main():
    timers = {}

    signal.signal(signal.SIGTSTP, handle_ctrl_z)

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
            print("\nbye.")
            break

main()