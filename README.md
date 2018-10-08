# Executor

A Process Management Console written in Python.

## Motivation

Network scanning, vulnerability scanning, and enumeration scripts all take time and resources to run. Some tools, like Nmap, can handle their own parallelization very well. Custom bash scripts, etc. are much more likely to be single threaded (or spawn everything in the background and quickly overwhelm your machine.)

Executor is a GUI + set of useful scripts + report creation tool that lets your run a single command (e.g. ping -c1 {target} ) across a large network of machines (100+) and organize the output per host in a way that is captured in an HTML report for easier consumption.

You set the maximum number of jobs to run at any time, queue up the jobs you want, and walk away as Executor starts jobs as soon as other jobs finish. THis makes it easier to queue up a lengthy sequence of scans to perform or scripts to run in the background as you triage and investigate the output of your first scans.

Executor could also be used for network administration. It is agnositc to the scripts being run or what a "target" is - it essentially equivalent to running xargs / gnu parallel, but with a GUI to kill / monitor / restart individual jobs and the ability for job to request a retry on failure.

A cli-only version may eventually happen.


# Dependencies

Yes. At a minimum, you need Python3, Tkinter, and psutil.
You also need XML::Simple from CPAN to use most the the scripts.

# Supported Platforms

Some features work on Windows, but the majority will only work on Linux. This tool as only been tested on Kali Linux.

# Quick Start Guide

Coming soon!


# Other Tools
Custom tools intended for educational / personal / non-malicous use.

# Disclaimer

All software is AS-IS, with no warranty provided or implied.
I accept no liability for misuse or damage caused by any tools hosted here.

Feel free to use them if you are so inclined and have permission from everyone you intend to scan.

