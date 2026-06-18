# timer-cli

A lightweight terminal timer manager with named timers, desktop notifications, speech alerts, and a Ctrl+Z mode switch. For personal use.

## What it does

* Create one-off timers
* Save reusable named timers
* Run multiple timers simultaneously
* Get desktop notifications when timers finish
* Hear spoken alerts via `spd-say`; But you can modify the notify function to do whatever you want
* View live timer progress in a dedicated status screen

## The cool part

Press **Ctrl+Z** to instantly switch between:

* **Input Mode** → enter commands
* **Timer Mode** → live dashboard showing all running timers

Instead of suspending the program, Ctrl+Z acts as a UI signal. One keystroke toggles between command entry and monitoring. I was too lazy for ANSI Codes or Raw Mode in terminal and all that jazz. Also I didn't want to use third party libraries. This is the quickest way I found.

## Requirements

* Python 3
* `notify-send`
* `spd-say`

## Usage

Run:

```bash
python timer.py
```

### Commands

Create a timer:

```text
set <hours> <minutes> <seconds>
```

Example:

```text
set 0 25 0
```

Create a reusable named timer:

```text
timer pomodoro 25m
```

Start a named timer:

```text
start pomodoro
```

Stop a running timer:

```text
stop <id>
```

Remove a timer:

```text
clear <id>
```

Save named timers:

```text
save
```

Show help:

```text
help
```

Quit:

```text
exit
```

## Duration Format

Named timers use:

```text
XhYmZs
```

Examples:

```text
30m
1h
1h30m
45s
2h15m10s
```

## Persistence

Named timers can be saved to:

```text
timers.json
```

and automatically loaded on startup.

## License

Do whatever you want with it. Time is limited anyway.
