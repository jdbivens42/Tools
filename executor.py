#!/usr/bin/python3
from tkinter import filedialog
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Notebook, Treeview, Progressbar
from tkinter.scrolledtext import ScrolledText
import os
import tempfile
from contextlib import contextmanager

from multiprocessing import Process, Manager, Queue
from multiprocessing.managers import BaseManager
from concurrent.futures import ThreadPoolExecutor

import subprocess
import psutil
from itertools import islice
import time
import statistics
import re
import queue
import random
import traceback

import dill #as pickle
dill.extend(True)

def browse(entry, exts, initialdir=None):
    exts = [("{} files".format(ext), "*.{}".format(ext) ) for ext in exts]
    exts.append(("all files","*.*"))
    
    filename = filedialog.askopenfilename(initialdir=initialdir, title = "Select file",filetypes = exts)
    if filename:
        entry.delete(0,END)
        entry.insert(0,filename)    
def load():
    global state
    loadConfig()

    #state['executor'].submit(loadTargets)
    state['executor'].submit(lambda x=not state['launched']: loadTargets(x))
    
    #state['check']['queued'] = True
    #state['changed']['queued'] = True

def readConfig(config_file):
    new_settings={}
    try:
        with open(config_file,'r') as config:
            for line in config:
                s=line.strip('\r\n\t')
                if s and s[0].isalpha():
                    try:
                        print("Attempting to load setting: {}".format(s))
                        arr = s.split('=', 1)
                        if len(arr) == 2:
                            if arr[0].startswith("CMD"):
                                new_settings[arr[0]] = arr[1]   #.strip('"\'')
                            elif arr[0].startswith("MAX_RUNNING") and state['changed_max_running']:
                                new_settings[arr[0]] = settings[arr[0]]
                            else:
                                new_settings[arr[0]] = arr[1].strip('"\'')
                                
                    except Exception as e:
                        print(e)
    except Exception as e:
        print("Exception: {}".format(e))
        return None

    return new_settings

def loadConfig():
    global settings
    global root
    global state
    
    tmp = readConfig(root.nametowidget("config_frame.config_entry").get())
    if not tmp:
        print("Settings failed to load!")
        return
    settings=tmp
    print("Settings Loaded:\n")
    
    for k,v in settings.items():
        print("{:20}{}{}".format(k,":"+" "*5,v))
        print("-"*80)
    try:
        spinbox = root.nametowidget("management_frame.max_running_spinbox")
        spinbox.delete(0, END)
        spinbox.insert(END, settings['MAX_RUNNING'])
            
        spinbox.configure(from_=0, to=999, command=updateMaxRunning, width='3') 
        spinbox.bind('<FocusOut>', updateMaxRunning, add='+')
        spinbox.bind('<Return>', updateMaxRunning, add='+')
        spinbox.bind('<KP_Enter>', updateMaxRunning, add='+')

    except Exception as e:
        print("MAX_RUNNING invalid: ")
        print(e)

def getTargetsFile():
    global root
    return root.nametowidget("config_frame.targets_entry").get()

# will throw away duplicate targets
def loadTargets(force=False):
    global jobs
    global settings
    global manager
    global root
    global state
    global targets_list
    
    if settings:
        if jobs:
            print("WARNING: Any duplicate or empty targets will be ignored! (Unclick the 'Launch' button to force)")
        else:
            jobs = {}
        
        #listbox = root.nametowidget("main_panel.status_frame.queued_frame.queued_listbox")
        #for c in listbox.get_children():
        #   if not c in jobs:
        #       listbox.delete(c)   
        
        try:
            targets_list = getTargetsFile()
            with open(targets_list,'r') as targets_file:
                if not manager:
                    print("manager false in loadTargets..")
                    BaseManager.register('Job', Job)
                    manager = BaseManager()
                    manager.start()
                    #manager.get_server().serve_forever()

                config_file = root.nametowidget("config_frame.config_entry").get()
                
                for line in targets_file:
                    if state['abort_load']:
                        print("Aborting async load!")
                        state['abort_load'] = False
                        return
                    s=line.strip('\r\n')
                    full_name = "{}\n({})".format(s, os.path.basename(config_file))

                    #WARNING: FORCING IS NOT SAFE - especially if the jobs is running - may lose control of running jobs
                    if s and (not full_name in jobs or force):
                        #print("S: {}".format(s))
                        #print("Full: {}".format(full_name))
                        jobs[full_name] = manager.Job(settings, (s, full_name), state['queue']['mgmt'])
                        #print("Putting {}".format(full_name))
                        #listbox.insert("", END, values=(s), iid=full_name)
                        state['queue']['move'].put(
                            lambda _j=full_name, _curr_list=None, _new_list='queued',  _tags=(), _values=(s):
                                moveTarget(_j, _curr_list, _new_list, _values, _tags )
                        )
            
                        state['queue']['queued'].put_nowait(full_name)
                    #elif s and force:
                    #    print("Attempting to force -- cross your fingers! (seriously though)")
                    #    #crazy dangerous, may desync gui with underlying data
                    #   state['selection'] = 
                        
                    else:
                        print("Job {!r} is already loaded. Use a different config file to duplicate jobs.".format(full_name))   
        except Exception as e:
            print(e)
        targets = list(jobs.keys())
        print("{} Target(s) Are Loaded.".format(len(targets)))
    else:
        print("Cannot load targets until settings are loaded!")





def chainLoad(config_file, target):
    global jobs
    global settings
    global manager
    global root
    global state
    global targets_list




    print("IN CHAIN_LOAD: {} {}".format(config_file, target))
    local_settings = readConfig(config_file)


    full_name = "{}\n({})".format(target, os.path.basename(config_file))

    #WARNING: FORCING IS NOT SAFE - especially if the jobs is running - may lose control of running jobs
    #if s and (not full_name in jobs or force):
    # CHAIN_LOAD will always force - super dangerous - don't chain load the same thing more than once
    if target:
        #print("S: {}".format(s))
        #print("Full: {}".format(full_name))
        if not manager:
            print("Manager is false in chainLoad...")
            BaseManager.register('Job', Job)
            manager = BaseManager()
            try:
                print("starting manager...")
                manager.start()
            except Exception as e:
                print(e)

        print("\n\nManager:\n{}\n\n".format(repr(manager)))

        jobs[full_name] = manager.Job(local_settings, (target, full_name), state['queue']['mgmt'])
        print("job: {} created in chain load".format(full_name))
        #print("Putting {}".format(full_name))
        #listbox.insert("", END, values=(s), iid=full_name)
        print(state['queue']['move'].qsize())
        state['queue']['move'].put(
            lambda _j=full_name, _curr_list=None, _new_list='queued',  _tags=(), _values=(target):
                moveTarget(_j, _curr_list, _new_list, _values, _tags )
        )
        print("Move request: {}".format(full_name))
        
        state['queue']['queued'].put_nowait(full_name)

        print("Queued: {}".format(full_name))
    #elif s and force:
    #    print("Attempting to force -- cross your fingers! (seriously though)")
    #   #ppppppppp
    #    #crazy dangerous, may desync gui with underlying data
    #   state['selection'] = 
        
    else:
        print("Job {!r} is already loaded. Use a different config file to duplicate jobs.".format(full_name))   



def saveAs(s, caller=None):
    if caller:
        caller.lower()  

    file = None
    try:
        file = filedialog.asksaveasfile(mode='wb')
        if file:
            file.write(s)
    except Exception as e:
        print("Save failed: {}".format(e))
    finally:
        if file:
            file.close()        

    if caller:
        caller.lift()

def exportItems(tv):
    iids = tv.get_children()
    saveAs(os.linesep.join([i.split('\n')[0] for i in iids]).encode())

def copyToClipboard(s):
    global root
    root.clipboard_clear()
    root.clipboard_append(s)

def copySelection(tv_name):
    global state
    items = [ t.split("\n")[0] for t in state['selection'][tv_name] ]
    # even on windows, using os.linesep doesn't work for copying - it adds two CRLF pairs
    s = "\n".join(items)
    print("{!r}".format(s))
    copyToClipboard(s)

def copySelectedText(tb):
    try:
        s = tb.get(SEL_FIRST,SEL_LAST)
        copyToClipboard(s)
    except Exception as e:
        pass

def selectAll(tv_name):
    global state
    state['selection'][tv_name] = []
    c_list = state['listbox'][tv_name].get_children()
    print("{} has children: {}".format(tv_name, c_list))
    state['selection'][tv_name].extend([c.split("\n")[0] for c in c_list])
    state['listbox'][tv_name].selection_add(c_list)
    print("seleciton: {}".format(state['selection']))

def selectAllText(tb):
    print("Selecting")
    tb.tag_add(SEL, "1.0", END)
    tb.mark_set(INSERT, "1.0")
    tb.see(INSERT)
    return 'break'
def toggleSelection(tv_name):
    global state
    c_list = state['listbox'][tv_name].get_children()
    c_count = len(c_list)
    if len(state['selection'][tv_name]) < c_count:
        selectAll(tv_name)
    else:
        state['selection'][tv_name] = []
        state['listbox'][tv_name].selection_remove(c_list)

def killProcess(pid):
    p = None
    try:
        p = psutil.Process(pid)
        # try to prevent the main subprocess from spawning additional children
        p.suspend()
    except Exception as e:
        print(e)
    finally:
        if p:
            b = False
            #while p.children(recursive=True):
            #print("PID {} IS SPAWNING NEW CHILDREN - MAY NOT BE ABLE TO FULLY KILL!".format(pid))
            for c in p.children(recursive=True):
                #print("CHLID: Killing {} / {}".format(c.pid, c.name))
                try:
                    c.kill()
                    #gone, alive = psutil.wait_procs([c], timeout=3, callback=lambda proc:print("{} killed".format(proc.pid)))
                    gone, alive = psutil.wait_procs([c], timeout=0)
                    #print(gone)
                    #print(alive)
                    #if alive:
                    #   #print("FATAL ERROR:\nPROCESSES {}\n COULD NOT BE KILLED - CONTINUE AT YOUR OWN RISK".format(alive))
                    #   for x in alive:
                    #       print(x.status())
                except Exception as e:
                    print(e)
                #time.sleep(0.1)
                b=True
            try:
                #print("PARENT: Killing {} / {}".format(p.pid, p.name))
                p.kill()
                #gone, alive = psutil.wait_procs([p], timeout=3, callback=lambda proc:print("{} killed".format(proc.pid)))
                gone, alive = psutil.wait_procs([p], timeout=3)
                #print(gone)
                if alive:
                    print("FATAL ERROR:\nPROCESSES {}\n COULD NOT BE KILLED - CONTINUE AT YOUR OWN RISK".format(alive))
                                    
            except Exception as e:
                    print(e)


def killJob(t, polite=False, move=True):
    global jobs
    global children
    global state
    prev = None
    try:
        prev = jobs[t].currList()
        jobs[t].kill(polite=polite)
        if not polite:
            if t in children and children[t]:
                print("Killing Parent Process {}".format(children[t].pid))
                killProcess(children[t].pid)
                try:
                    children[t].join(1)
                except Exception:
                    print("Failed to join with child")
                    pass

    except psutil.NoSuchProcess as e:
        print(e)
    except Exception as e:
        print("ERROR KILLING:\n{}\n{}".format(t, e))
    
    try:
        if t in children:
            del children[t]
        if t in state['running_dict']:
            del state['running_dict'][t]
        if t in state['update_dict']:
            del state['update_dict'][t]


        if prev and (jobs[t].currList() == 'failed' or move):
            #print("\nMOVE {} -> {}".format(prev, 'failed'))
            state['queue']['move'].put(
                lambda _j=t, _curr_list=prev, _new_list='failed',  _tags=('canceled'), _values=(t):
                    moveTarget(_j, _curr_list, _new_list, _values, _tags )
            )
    except Exception as e:
        print("ERROR CLEANING UP AFTER KILLING:\n{}\n{}".format(t, e))
    

def requeueJob(target):
    global jobs
    global state
    try:
        if target in jobs:
            job = jobs[target]
            if job.isDone() and job.currList() in ['failed', 'finished'] and not target in state['running_dict']:
                curr_list = job.currList()
                job.setStatus('queued')
                job.revive()
                state['queue']['move'].put(
                    lambda _j=target, _curr_list=curr_list, _new_list='queued',  _tags=(), _values=(target.split("\n")[0]):
                        moveTarget(_j, _curr_list, _new_list, _values, _tags )
                )
            
                state['queue']['queued'].put(target)
                print("{} requeued!".format(target))    
            else:
                print("REQUEUE FAILED: {} cannot be requeued right now".format(target))
                print("Ensure that it is FAILED or FINISHED before requeuing")
    except Exception as e:
        print(type(e).__name__)
        print(e)

def inspectJob(evt):
    global jobs
    global root
    global state
    w = evt.widget
    selection = w.selection()
    k = str(w).split(".")[-1].split('_')[0]
    if selection:
        #print("Selected: {}".format(selection))
        state['selection'][k] = list(selection)
        
        selection = selection[0]
        if selection:
            reloadJobFrame(root, selection)
    else:
        state['selection'][k] = []
    
    #print(state['selection'])

@contextmanager
def tmpFile():
    tmp_file = None
    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, mode="wb")
        name = tmp_file.name
        tmp_file.close()    
        yield name
    finally:
        os.unlink(tmp_file.name)

def startManagedJob(managed_job):
    global children
    global settings
    global state

    try:
        #print("starting {}".format(managed_job.getTarget()))
        target = managed_job.getTarget()
    

        if managed_job.isSleeping():
            managed_job.resume()
        else:
            if target in children:
        
                try:
                    children[target].join(1)
                except Exception:
                    print("Old child for {} unresponsive; killing it".format(target))
                    killProcess(children[target].pid)
                    children[target].join(1)

            managed_job.setStatus("running")
            p = Process(target=managed_job.start, args=())
            #print("\n\nStarting {}\n".format(target))
            p.start()
            children[target] = p

    except Exception as e:
        print("\n\nFATAL ERROR: Job Start Failed!")
        print(e)
    
        print("\n\nHOST SYSTEM CRASH IMMINENT") 
        #print("Decreasing MAX_RUNNING to try to recover...")
        #settings['MAX_RUNNING'] = 0
        print("DISABLING LAUNCH")
        state['launched'] = False
class Job:
    def __init__(self, settings, target_tuple, mgmt_q):     
        self.mgmt_q = mgmt_q
        self.sub_proc = None
        self.killed = False
        self.stats={}
        self.attempt = 0
        self.status="QUEUED_{}".format(self.attempt)
        self.prev_status = self.status
        self.target_full = target_tuple[1]
        self.target =  target_tuple[0]
        
        self.settings = settings.copy()
        self.unprimed_settings = settings.copy()
        #self.prime(1, None)
        self.starttime = None   
        self.elapsed_active = 0
        self.lastsitrep = 0 
        self.stoptime = None
        self.alarmclock = None
        self.sleeping = False

        self.num_stages = len([k for k in self.settings if k.startswith("CMD_") ])
    def start(self):
        try:
            self.alarmclock = None
            if self.attempt == 0:
                self.starttime = time.time()
            else:
                self.stoptime = None
            if not self.killed:

                self.status = "RUNNING_1"
                #self.attempt = 0
                with tmpFile() as outfile, tmpFile() as stdout, tmpFile() as stderr:
                    self._start(outfile, stdout, stderr)
                    #print("Exiting start!")
                self.stoptime = time.time()
        except Exception as e:
            print("FATAL ERROR: JOB DEATH - {}".format(self.target))
            print("{}: {}".format(type(e).__name__, e))
            
            print(traceback.format_exception(type(e), e, e.__traceback__),
                file=sys.stderr, flush=True)

            self.status="FAILED"
    
    def _start(self, outfile, stdout, stderr):
        if self.attempt > 0:
            self.attempt = self.attempt + 1
        else:
            self.attempt = 1
        #print("{} Attempt {}".format(self.target, self.attempt))
        self.stats[self.attempt] = {}
                
        #print("Resources for job {}:".format(self.target))
        #print("{}\n{}\n{}\n".format(outfile, stdout, stderr))
        
        resources = {'outfile':outfile,'stdout':stdout,'stderr':stderr}
        stage = 1
        while stage:
            #print("On Stage {}".format(stage))
            stage = self.execWrapper(stage, resources)
            #print("Stage: {}".format(stage))
            if stage and stage > self.num_stages:
                self.status="FINISHED_{}".format(self.attempt)

                #CHECK FOR CHAIN_LOAD
                if "CHAIN_LOAD_CONFIG" in self.settings:
                    print("Following next link in CHAIN_LOAD...")
                    print("Priming - Config: {} Target: {}".format(self.settings["CHAIN_LOAD_CONFIG"], self.settings["CHAIN_LOAD_TARGET"]))
                    self.__prime(stage, resources, "CHAIN_LOAD_CONFIG")
                    self.__prime(stage, resources, "CHAIN_LOAD_TARGET")
                    print("Primed - Config: {} Target: {}".format(self.settings["CHAIN_LOAD_CONFIG"], self.settings["CHAIN_LOAD_TARGET"]))
                    #self.chainLoad(self.settings["CHAIN_LOAD_CONFIG"], self.settings["CHAIN_LOAD_TARGET"])
                    #self.mgmt_q.put(
                    #    lambda c=self.settings["CHAIN_LOAD_CONFIG"], t=self.settings["CHAIN_LOAD_TARGET"]: chainLoad(c, t)
                    #)

                    #Lambdas aren't pickleable :/
                    task = ("chainLoad", self.settings["CHAIN_LOAD_CONFIG"], self.settings["CHAIN_LOAD_TARGET"]) 
                    self.mgmt_q.put(
                        task
                    )
                    
                    print ("CHAIN_LOAD queued task {}!".format(task))
                break

    def __flush(self, filename):
        #if self.settings['STDOUT_PLACEHOLDER'] in self.unprimed_settings['CMD_']:
        with open(filename, 'wb') as f:
            f.write(msg_out)
            #print("Wrote:\n{}\n\nTo:{}".format(msg_out, resources['stdout']))

    def execWrapper(self, stage, resources):
        ret_val = stage + 1
        expired = False

        if self.killed:
            self.status="FAILED_{}_USER".format(self.attempt)
            return None

        res, msg_out, msg_err = self.exec(stage, resources)


        #print("{}: {} ret {}".format(self.target, stage, res))
        if self.killed:
            #print("Killed!")
            self.status="FAILED_{}_USER".format(self.attempt)
            ret_val = None
        elif res is None or res != 0:
            # failed
            #print("{} failed".format(self.target))
            k = 'ONFAIL_{}'.format(stage)
            if self.settings[k] == "RESCHEDULE":
                reschedule_max = int(self.settings['RESCHEDULE_MAX'])
                if reschedule_max == 0 or self.attempt < 1 + reschedule_max:
                    reschedule_ttl = int(self.settings['RESCHEDULE_TTL'])
                    if reschedule_ttl == 0 or (time.time() - self.starttime) < reschedule_ttl:
                        self.status="RESCHEDULED_WAIT"
                        self.alarmclock = int(time.time()) + int(self.settings['RESCHEDULE_DELAY'])
                        #self.attempt = self.attempt+1
                    else:
                        print("RESCHEDULE_TTL exceeded for {}".format(self.target))
                        expired = True
                else:
                    print("RESCHEDULE_MAX reached for {}".format(self.target))
                    expired = True
                        
                ret_val = None
        
            elif self.settings[k] == "SLEEP":
                ret_val = stage

                sleep_max = int(self.settings['SLEEP_MAX'])
                if sleep_max == 0 or self.attempt < 1 + sleep_max:
                    #print("Job {} failed but will retry after sleeping".format(self.target))

                    #block here
                    if not self.sleepUntilReady():
                        #job woke but was killed while sleeping
                        ret_val = None
                else:
                    print("SLEEP_MAX exceeded for {}".format(self.target))
                    expired = True

            elif self.settings[k] == "IGNORE":
                pass
            else:
                self.status="FAILED_{}".format(stage)
                ret_val = None

            if expired:
                self.status="FAILED_{}".format(stage)   
                ret_val = None

        # only persist to disk if we are continuing TO A DIFFERENT STAGE (or we are chain loading)
        # and a future stage has requested this output
        if ret_val and ret_val != stage and ret_val <= self.num_stages:
            out = self.settings['STDOUT_PLACEHOLDER']
            err = self.settings['STDERR_PLACEHOLDER']

            if ret_val == self.num_stages + 1 and "CHAIN_LOAD_CONFIG" in self.settings:
                print("Beginning CHAIN_LOAD...")
                if out in self.unprimed_settings['CHAIN_LOAD_CONFIG'] or out in self.unprimed_settings['CHAIN_LOAD_TARGET']:
                    self.__flush(resources['stdout'])

                if err in self.unprimed_settings['CHAIN_LOAD_CONFIG'] or err in self.unprimed_settings['CHAIN_LOAD_TARGET']:
                    self.__flush(resources['stderr'])
              
            # CMD_{} is not safe for chain loading (key error) - chain loading handled above                  
            else:
                if out in self.unprimed_settings['CMD_{}'.format(ret_val)]:
                    self.__flush(resources['stdout'])

                if err in self.unprimed_settings['CMD_{}'.format(ret_val)]:
                   self.__flush(resources['stderr'])

        return ret_val

    def exec(self, stage, resources):
        #if stage > 1:
        #self.status="PRIMING_{}".format(stage)
        self.prime(stage, resources)

        self.status="RUNNING_{}".format(stage)

        cmd = self.settings["CMD_{}".format(stage)]
        shell = self.settings["SHELL_{}".format(stage)]
        
        msg_out = b""
        msg_err = b""
        ret_code = 0
        #print("Invoking {!r}".format(cmd))
        
        proc = None
        timeout = None
        if self.settings["TIMEOUT_{}".format(stage)] != "0": 
            timeout = int(self.settings['TIMEOUT_{}'.format(stage)])

        env = os.environ.copy()

        with open(os.path.join(script_dir, "executor.env.default" ), "r") as env_conf:
            for e in env_conf:
                e = e.strip()
                k,v = e.split("=",1)
                env[k]=v
        try:


            env_custom = os.path.join(os.path.dirname(targets_list) , "executor.env")

            with open(env_custom, "r") as env_conf:
                for e in env_conf:
                    e = e.strip()
                    k,v = e.split("=",1)
                    env[k]=v

        except Exception as e:
            print("WARNING: executor.env not defined for the target directory")
            env["EXECUTOR_OUTDIR"] = os.path.dirname(targets_list)
            print("Set outdir to {}".format(env["EXECUTOR_OUTDIR"]))



        if cmd:
            if os.name == 'posix':
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, close_fds=True, env=env)
            else:
                #patch: hide cmd popup on windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, startupinfo=startupinfo, env=env)

            self.sub_proc = proc
            #print(self.sub_proc)
            
            try:
                msg_out, msg_err = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                print("Timeout expired for {}".format(self.target))
                killProcess(proc.pid)
                try:
                    msg_out, msg_err = proc.communicate(timeout=1)
                except subprocess.TimeoutExpired:
    
                    pass

                proc = None
            if proc:
                ret_code = proc.returncode 
            else:
                ret_code = None

        self.sub_proc = None
    
        #print("Returned: {}".format(ret_code))
        #res_tuple = (stage, ret_code, msg_out, msg_err)
        #print("Result tuple: {}".format(res_tuple))
        
        #self.return_codes.append(res_tuple)
        #self.stats[self.attempt][stage] = {}
        self.stats[self.attempt][stage]['ret_code'] = ret_code
        self.stats[self.attempt][stage]['msg_out'] = msg_out
        self.stats[self.attempt][stage]['msg_err'] = msg_err

        return ret_code, msg_out, msg_err


    def resume(self):
        self.sleeping=False
        self.attempt = self.attempt + 1
        self.stats[self.attempt] = {}
    def sleepUntilReady(self):
        # look at status and settings
        # block in this function until we were given permission to run
        # or realize that we have been killed

        # NOTE TO SELF: if this job is "started" again, that would be bad
        # this process can't exit because it has resources that might be needed
        # assert sleeping, and have StartManagedJob call resume instead of start
        self.status = "SLEEPING_WAIT"
        self.sleeping = True
        self.alarmclock = time.time() + int(self.settings['SLEEP_DELAY'])
        time.sleep(int(self.settings['SLEEP_DELAY']))
        self.status = "SLEEPING_READY"
        while self.sleeping and not self.killed:
            time.sleep(1)

        return not self.killed

    def isSleeping(self):
        return self.sleeping
    
    def __prime(self, stage, resources, k):
        # unprimed_settings must be used to allow new resources to be injected in the event of reschedule
        self.settings[k] = self.unprimed_settings[k].replace(self.settings["TARGET_PLACEHOLDER"], self.target)
        #if stage==2:
        #   self.settings[k] = self.settings[k].replace(self.settings["TMP_PLACEHOLDER"], resources['outfile'])
        #elif stage==3:
        self.settings[k] = self.settings[k].replace(self.settings["TMP_PLACEHOLDER"], resources['outfile'])
        self.settings[k] = self.settings[k].replace(self.settings["STDOUT_PLACEHOLDER"], resources['stdout'])
        self.settings[k] = self.settings[k].replace(self.settings["STDERR_PLACEHOLDER"], resources['stderr'])

        #if stage>1:
        #    # this is the most recent return code returned by. This should never throw a key error,
        #    # since stage x+1 must never be called unless stage x completed         
        #    self.settings[k] = self.settings[k].replace(
        #        self.settings["RET_PLACEHOLDER"],
        #        str(self.stats[self.attempt][stage-1]['ret_code'])
        #    )  

        # this is the most recent return code returned by. This should never throw a key error,
        #    # since stage x+1 must never be called unless stage x completed         
        # -- is this still true for chain loading? probably?
        try:
            if stage>1:
                self.settings[k] = self.settings[k].replace(
                self.settings["RET_PLACEHOLDER"],
                    str(self.stats[self.attempt][stage-1]['ret_code'])
                )
        except Exception as e:
            print("RET_PLACEHOLDER replacement failed")
            print("Stage: {} resources:{} k:{}".format(stage, resources, k))
            print(e)


    def prime(self, stage, resources):
        k="CMD_{}".format(stage)
        self.__prime(stage, resources, k)

        cmd = self.settings[k]
        shell = self.unprimed_settings["SHELL_{}".format(stage)]
        delim = self.unprimed_settings["DELIM_{}".format(stage)]
        
        if shell == 'FALSE':
            if cmd:
                self.settings[k] = cmd.split(delim)
            self.settings["SHELL_{}".format(stage)] = False
        else:
            self.settings["SHELL_{}".format(stage)] = True
        
        self.stats[self.attempt][stage] = {}

    def sitrep(self):
        prev = self.prev_status
        # there is currently no listbox for priming (it should be extremely fast), so don't report it
        curr = self.status.replace("SLEEPING_WAIT", "RUNNING_SLEEP").replace("SLEEPING_READY", "RUNNING_SLEEP")     #.replace("PRIMING", "RUNNING")
        #curr = self.currList()

        #if curr.startswith("RUNNING"):
        #   curr = "RUNNING"    
        
        now = time.time()
        if self.starttime and not self.stoptime and not self.prev_status.startswith(('SLEEPING', 'RESCHEDULED')):
            if self.lastsitrep:
                self.elapsed_active = self.elapsed_active + (now - self.lastsitrep)
            else:
                self.elapsed_active = self.elapsed_active + (now - self.starttime)

        #elif self.status == "RESCHEDULED_WAIT":
        #   if now > self.alarmclock:
        #       self.status="RESCHEDULED_READY"
        #       curr = "RESCHEDULED_READY"
        self.lastsitrep = now

        # update prev_status to the last reported status
        self.prev_status = curr
        
        return (prev, curr, self.elapsed_active)




    def getStatus(self):
        return self.status

    def currList(self):
        s = self.status.split("_")[0].lower()
        return s.replace('sleeping', 'running')

    def getLastSitrep(self):
        if self.lastsitrep == 0:
            self.lastsitrep = time.time()
        return self.lastsitrep

    def setStatus(self, prefix):
        self.prev_status = prefix
        suffix = self.attempt
        if prefix == 'running':
            suffix = 0
        self.status = "{}_{}".format(prefix, suffix)
    def getElapsed(self):
        return self.elapsed_active

    def getTimes(self):
        return (self.starttime, self.stoptime)

    def revive(self):
        self.killed = False
        print("{} revived".format(self.target))
    def kill(self, polite=False):
        self.killed = True
        print("Killing Job: {}".format(self.target))
        
        if polite==True:
            print("(Politely)")
        else:
    
            if self.sub_proc:
                #print('Subproc name: {}'.format(psutil.Process(self.sub_proc.pid).name()))
                killProcess(self.sub_proc.pid)
                self.sub_proc = None

            else:
                print("No active subprocess")
        if self.status.startswith(('QUEUED', 'RESCHEDULED')):
            print("Job {} is not currently active - updating status".format(self.target))
            self.status = "FAILED_CANCELED"

    def getTarget(self):
        #print(self.target_full)
        return self.target_full

    def getStats(self):
        return self.stats   #.copy()    

    def isDone(self):
        return self.status.upper().startswith(('FINISHED', 'FAILED', 'RESCHEDULED'))

    def getAlarm(self):
        return self.alarmclock
    
    def isReady(self):
        prev, curr, elapsed = self.sitrep()
        return curr.split("_")[1] != "WAIT"
    def isKilled(self):
        return self.killed
def moveTarget(target, prev, curr, values, tags):
    global jobs
    global state
    prev_listbox = None
    if prev:
        prev_listbox = state['listbox'][prev]
    curr_listbox = state['listbox'][curr]

    #print ("\n50MOVING: {}\nFrom {} to {}".format(target, prev, curr))
    #print(values)
    try:
        if prev_listbox:
            prev_listbox.delete(target)
    except Exception as e:
        #print("Delete {} / {} failed".format(target, prev_listbox))
        pass
    else:
        try:
            curr_listbox.insert("", END, iid=target, values=values, tags=tags)
        except Exception:
            print("GUI Insert {} / {} failed -- deleting and adding".format(target, prev_listbox))
            curr_listbox.delete(target)
            curr_listbox.insert("", END, iid=target, values=values, tags=tags)

        if prev and target in state['selection'][prev]:
            try:
                if target in state['update_dict']:
                    del state['update_dict'][target]

            except Exception:
                pass

            state['selection'][prev].remove(target)
        
            state['selection'][curr].append(target)
            curr_listbox.selection_add(target)

        #if curr=='rescheduled':
        #   state['queue']['rescheduled'].put_nowait(
        #       lambda: enqueueWhenReady("{}_ready".format(curr), target)
        #   )
#       if curr == 'rescheduled':
#           state['rescheduled_ready'].append(jobs[target].getAlarm())
#       elif prev == 'rescheduled':
#           state['rescheduled_ready'].remove(jobs[target].getAlarm())

################ might be needed
        #jobs[target].setStatus(curr.upper())

    # thread safe?
    #state['changed'][prev] = True
    #state['changed'][curr] = True


def updateItems():
    global state
    global settings

    global root
    if not settings:
        root.after(1000, updateItems)
        return
    for i in range(len(state['update_dict'])):
        try:
            target, data = state['update_dict'].popitem()
            listbox, values, tags = data
            root.after_idle(lambda t=target, l=listbox, v=values, tags=tags: updateItem(t, l, v, tags))
        except Exception:
            break

    root.after(int(settings['REFRESH_DELAY']), updateItems)

def updateItem(target, listbox, values, tags):
    try:
        listbox.item(target, values=values, tags=tags)
    except Exception:
        pass

def guiQueueConsumer(name):
    global state
    global root
    global settings

    if not settings:
        root.after(1000, lambda: guiQueueConsumer(name))
        return
    #print("{} Depth: {}".format(name, state['queue'][name].qsize()))
    while True:
        try:
            task = state['queue'][name].get(block=False)
        except queue.Empty:
            break
        else:
            root.after_idle(task)

    root.after(int(settings['REFRESH_DELAY']), lambda: guiQueueConsumer(name))

def invokeTask(task, qname):
    try:
        if qname =="mgmt" and type(task) is tuple:
            globals()[task[0]]( *task[1:] )
        else:
            task()
    except Exception as e:
        print("TASK FAILED:")
        print(traceback.format_exception(type(e), e, e.__traceback__),
        file=sys.stderr, flush=True)
        
        

def queueConsumer(name):
    global state
    submit = False

    while True:
        if name == 'mgmt':
            print("Management Queue init!")
            print(state['queue'][name])
        #print("{} Depth: {}".format(name, state['queue'][name].qsize()))
        task = state['queue'][name].get(block=True)
        
        if state['quit']:
            #print("{} is quiting".format(name))
            break

        if name != 'sitrep':
           print("{} popped {}".format(name, task))

        if name == "mgmt":
            print("Management Queue Task: {}".format(task))

        #if name != 'sitrep':
        #   print("{} popped {}".format(name, task))
        #if type(task) is tuple:
        elif name == 'sitrep':

            #if not submit and time.time() - task[0] > 0.1:
            if state['queue']['sitrep'].qsize() > NUM_CHECKERS*state['executor']._work_queue.qsize():
            #   #print("{} ({}) seconds behind!".format(task[0], time.time() - task[0]))
                submit = True
            else:
                submit = False
            task = task[-1]


        if submit:
            #print("submitting getSitRep")
            state['executor'].submit(task)
        else:
            invokeTask(task, name)
#need one for rescheduled and one for sleeping
def enqueueWhenReady(dest, target):
    global jobs
    global state
    if target in jobs:
        then = None
        try:
            then = jobs[target].getAlarm()
        except Exception:
            pass
        if not then:
            return
        while time.time() < then:
            #time.sleep(jobs[target].getAlarm() - time.time())
            #print("Sleeping for {} seconds longer".format(then - time.time()))
            time.sleep(5)
            #can't sleep the entire duration or the threadpool will block on this thread indefinitely
            if state['quit']:
                return
        state['queue'][dest].put_nowait(target)


def getSitrep(target):
    global jobs
    global state
    global children
######################################  CHECK FOR SLEEPING, don't create a move, just pop from running_dict and change tag



    #print("Updating {}".format(target))
    if target in jobs:
        job = jobs[target]
        last_sitrep = job.getLastSitrep()
        #print(last_sitrep)
        prev, curr, elapsed = job.sitrep()
        #print("{} / {} @ {}".format(prev, curr,elapsed))


        base_prev = prev.split("_")[0].lower()
        base_curr = curr.split("_")[0].lower()


        prev_listbox = state['listbox'][base_prev]  #root.nametowidget(prev_name)
        curr_listbox = state['listbox'][base_curr]  #root.nametowidget(curr_name)

        target_nickname = target.split("\n", 1)[0]

        #print("Nickname: {}".format(target_nickname))

        if base_curr != base_prev:
            #print("Update for {}: {} / {}".format(target, prev, curr))
            values = (target_nickname)
            tags = ()
            if base_curr == 'running':
                values = (target_nickname, '...')
                tags = 'stage_{}'.format(curr.lower().split('_')[-1])

            
    ###########TODO: Never ask to be moved to running - checkProgress must do this and ensure that the job will not ask for this move       
            #curr_list = job.currList()
            
            #print ("\n\nSCHEDULED: {}\nFrom {} to {}".format(target, base_prev, base_curr))
            #def moveTarget(target, prev, curr, values, tags):
            #print("MOVE REQUEST: {} {} {} {} {}".format(target, base_prev, base_curr,tags, values))
            state['queue']['move'].put(
                lambda _j=target, _curr_list=base_prev, _new_list=base_curr,  _tags=tags, _values=values:
                    moveTarget(_j, _curr_list, _new_list, _values, _tags )
            )

            try:
                state['running_dict'].pop(target)
            except Exception:
                pass
            else:
                if base_curr == 'rescheduled':
                    state['queue'][base_curr].put_nowait(
                        lambda: enqueueWhenReady("{}_ready".format(base_curr), target)
                    )

                    
            #updateCounts([base_prev, base_curr])
        elif base_curr == 'running':
            #print("Status of {}: {} / {}".format(target, prev, curr))
            tag = 'stage_{}'.format(curr.lower().split('_')[1])
            progress = '...'
            if state['stats']['mode'] == 'determinate' and tag != 'stage_0':
                # The higher this is, the more pessimistic the estimations are / the more confident that
                # the job will be finished by the current 'deadline'
                pessimism_factor = 1.25
                deadline = state['stats']['mean'] + pessimism_factor*state['stats']['std_dev']
                if deadline != 0:
                    progress = "~{:.0f}%".format(min(100 * elapsed / deadline, 99))
            
            #curr_listbox.item(target, values=(target_nickname, progress), tags=tag)
            values = (target_nickname, progress)
            #print("Tagging with{}".format(tag))        
            state['update_dict'][target] = (curr_listbox, values, tag)
            

            if target in jobs and job.isSleeping():
                #print("Job is sleeping!")
                try:
                    state['running_dict'].pop(target)
                except Exception:
                    pass
                else:
                    #print("Pop succeeded")
                    state['queue']['sleeping'].put_nowait(
                        lambda t=target: enqueueWhenReady("sleeping_ready", t)
                    )
                    #print("Put succeeded")
            elif target in jobs and not job.isKilled():
                state['queue']['sitrep'].put(
                    (last_sitrep, random.random(), lambda t=target: getSitrep(t))
                )
            #print("UPDATE PUT")
        if target in jobs and job.isDone() and not target in state['running_dict']:
            #print("TARGET IS DONE")
            state['stats']['elapsed'][target] = elapsed
            
            try:
                if target in children and children[target]:
                    #print("Collecting child for {}".format(target))
                    children[target].join(1)
                    del children[target]
            except Exception as e:
                print("{}: {}".format(type(e).__name__, e))
                if target not in children or target in state['running_dict']:
                    pass #print("All good!")
                else:
                    print("Child for {} unresponsive; Kill if this does not self correct".format(target))
            
                #killJob(target)
            #print("Done!\n\n")

        else:
            state['stats']['elapsed'][target] = elapsed + state['stats']['std_dev']
            

        #print("RETURNING") 

def sortTreeviewColumn(root, name,  _col, reverse):
    tv = root.nametowidget(name)

    l = [(tv.set(k, _col), k) for k in tv.get_children('')]

    if all(re.match(r"((\W+)?(\d+)?)+", t[0]) for t in l):
        print("Data appears mostly numeric - trying to sort numerically (IP mode)")
        #print([tuple(re.split(r"\W+", t[0])) for t in l])
        try:
            l.sort(reverse=reverse, key=lambda t: tuple( [int(i) for i in re.split(r"\W+", t[0]) if i ]))
        except Exception as e:
            print(e)
            l.sort(reverse=reverse)
    else:
        l.sort(reverse=reverse)
    
    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # reverse sort next time
    tv.heading(_col, command=lambda: sortTreeviewColumn(root, name, _col, not reverse))

def updateStats():
    global state
    global jobs
    vals = list(state['stats']['elapsed'].values())
    if vals and len(vals) > 2:
        state['stats']['mean'] = statistics.mean(vals)
        state['stats']['std_dev'] = statistics.stdev(vals)

        if any(j.isDone() for j in list(jobs.values())):
            state['stats']['mode'] = 'determinate'

    #print("Mean: {}\nStd Dev: {}".format(state['stats']['mean'], state['stats']['std_dev']))


def getContents(root, treeview_name):
    tv = root.nametowidget(treeview_name)
    iids = tv.get_children()
    #return [tv.item(i, "text") for i in iids]
    return list(iids)


def launch(button_frame):
    global state
    b = button_frame.nametowidget('launch')
    state['launched'] = not state['launched']
    if state['launched']:
        b.config(relief=SUNKEN)
    else:
        b.config(relief=RAISED)
    
    #checkProgress()

def onIdle(func):
    global root
    root.after_idle(func)

def flushIdle():
    global root
    global settings
    
    if not settings:
        root.after(1000, flushIdle)
        return

    #print("Refreshing...")
    root.update_idletasks()
    #print("Done!")
    root.after(int(settings['REFRESH_DELAY']), flushIdle) 
# scheudle separately 
def updateCounts(names):
    global state
    global root
    global settings
    global jobs

    if not settings:
        root.after(1000, lambda names=names: onIdle(lambda names=names: updateCounts(names) ))
        return

    for name in names:
        label = state['label'][name]
        listbox = state['listbox'][name]
    
        text = ""
        if name == 'running':
            r = 0
            s = 0
            for c in listbox.get_children():
                if jobs[c].isSleeping():
                    s = s + 1
                else:
                    r = r + 1
            text =  "{}: {} / {}: {}".format(name.title(), r, 'Sleeping', s)
        else:
            text = "{}: {}".format(name.title(), len(listbox.get_children()))


        label['text'] = text
    
    root.after(settings['REFRESH_DELAY'], lambda names=names: onIdle(lambda names=names: updateCounts(names) ))

def checkFree():
    global jobs
    global root
    global children
    global settings
    global state

    while not state['quit']:
        try:
            #print("\nChecking Free...")    
            #print("Executor queue depth: {}".format(state['executor']._work_queue.qsize()))
            #print("Sitrep queue depth: {}".format(state['queue']['sitrep'].qsize()))
            #try:
            #   print("Sitrep peek {}".format(time.time() - state['queue']['sitrep'].queue[0][0]))
            #except Exception as e:
            #   #print(e)
            #   pass

            updateStats()
            
            if state['launched']:
                
                num_free = 0
            
                num_free = int(settings['MAX_RUNNING']) - len(state['running_dict'])
                #print("Free: {}".format(num_free))         
                
                if num_free > 0:
                    
                    ######GET SLEEPING, highest priority    

        #######################################  SLEEPING

                    rescheduled = state['queue']['rescheduled_ready']
                    queued = state['queue']['queued']
            
                    
                    candidates = [rescheduled, queued]
                    curr_list = ['rescheduled', 'queued']
                    spawned = 0
                    for i in range(num_free):
                        j = None
                        q = state['queue']['sleeping_ready']
                        try:
                            j = q.get(block=False)
                            while j not in jobs or jobs[j].isKilled() or j in state['running_dict']:
                                print("Purging old job from queue...")
                                j = None
                                j = q.get(block=False)

                        except queue.Empty:
                                

                            for i in range(len(candidates)):
                                try:
                                    j = candidates[0].get(block=False)
                                    while j not in jobs or jobs[j].isKilled() or j in state['running_dict']:
                                        print("Purging old job from queue...")
                                        j = None
                                        j = candidates[0].get(block=False)
                                    if j:
                                        #print("job not killed")
                                        break
                                except queue.Empty:
                                    pass

                                candidates.append(candidates.pop(0))
                                curr_list.append(curr_list.pop(0))
                        if j:
                            #print("Job:\n{}\nPopped from {}".format(j, curr_list[0]))
                            #state['queue']['running'].put(j)
                            state['running_dict'][j] = jobs[j]

                            startManagedJob(jobs[j])
                            spawned = spawned + 1
                            nickname = j.split("\n")[0]

                            # produce GUI task
                            state['queue']['move'].put(
                                lambda _j=j, _curr=curr_list[0], _nickname=nickname:
                                    moveTarget(_j, _curr, 'running', (_nickname, '...' ), () )
                            )
                
                            # produce non-GUI task
                            # could block, but only should under the most extreme circumstances where producers are flooding consumers with mostly redundant work
                            state['queue']['sitrep'].put(
                                (time.time(), random.random(), lambda _j=j: getSitrep(_j) )
                            )
                    if spawned > 0:
                        print("Spawned {} jobs".format(spawned))
            time.sleep(1)
        except Exception as e:
            print("UNEXPECTED ERROR OCCURRED: {}".format(e))
            print("Trying to ignore")


def addCommandFrame():
    pass
def removeCommandFrame():
    pass
def attachPlaceholdersFrame(root):
    pass
def attachRescheduleFrame(root):
    pass
def atatchSleepFrame(root):
    pass
def attachGeneralFrame(root):
    pass

def helpBox(x):
    s = state['help'][x]
    messagebox.showinfo(x, s, parent=state['config_editor'])



def labeledWidget(root, label_text, help_name):
    lbl = Label(root, text=label_text, anchor=CENTER)
    b = Button(root, text="?", command=lambda n=help_name: helpBox(n))
    return (lbl, b)



def labeledEntry(root, label_text, entry_name, default_val, help_name):
    global state

    lbl, b = labeledWidget(root, label_text, help_name)

    state['config_vals'][entry_name] = StringVar()
    
    e = Entry(root, textvariable=state['config_vals'][entry_name])
    
    state['config_vals'][entry_name].set(default_val)
    return (lbl, e, b)

def labeledSpinbox(root, label_text, spinbox_name, from_, to, default_val, help_name):
    lbl, b = labeledWidget(root, label_text, help_name)

    state['config_vals'][spinbox_name] = IntVar()
    spinbox = Spinbox(root, textvariable=state['config_vals'][spinbox_name], from_=from_, to=to)

    state['config_vals'][spinbox_name].set(default_val)
    

    return (lbl, spinbox, b)

def editorClose():
    global root
    global state
    print("\nDone")
    root.grab_set()
    state['config_editor'].withdraw()
            

def changeShellMode(i):
    global state
    arr = [state['config_vals']['cmd_{}_argframe'.format(i)],
        state['config_vals']['CMD_{}_SHELL'.format(i)]
    ]
    if state['config_vals']['SHELL_{}'.format(i)].get() == "TRUE":
        arr.reverse()
    arr[0].grid()
    arr[1].grid_remove()

def nextArg(argframe, cmd, button_prev, button_next, e_list):
    sv = StringVar()
    curr = len(e_list)
    sv.set("arg{}".format(curr))

    state['config_vals']['CMD_{}_ARG_{}'.format(cmd, curr)] = sv
        
    e = Entry(argframe, textvariable=sv, width=5)
    print(curr)
    e.grid(row=0, column=curr, sticky=E+W)  
    e_list.append(e)
    Grid.columnconfigure(argframe, curr, weight=1)

    
    button_prev.configure(command=lambda argframe=argframe, cmd=cmd, button_prev=button_prev,  button_next=button_next, e_list=e_list: prevArg(argframe, cmd,  button_prev, button_next, e_list))
    button_prev.grid_remove()
    button_prev.grid(column=curr+1, sticky=E)   

    button_next.configure(command=lambda argframe=argframe, cmd=cmd, button_prev=button_prev, button_next=button_next,  e_list=e_list: nextArg(argframe, cmd, button_prev, button_next, e_list))
    button_next.grid_remove()
    button_next.grid(column=curr+2, sticky=W)   


    Grid.columnconfigure(argframe, curr, weight=1)


    Grid.columnconfigure(argframe, curr+1, weight=0)
    Grid.columnconfigure(argframe, curr+2, weight=0)

    print("-: {}".format(curr+1))
    print("+: {}".format(curr+2))


def prevArg(argframe, cmd, button_prev, button_next, e_list):
    curr = len(e_list)
    if curr > 1:

        e_list.pop().grid_forget()
        del state['config_vals']['CMD_{}_ARG_{}'.format(cmd, curr-1)]
        
        button_prev.configure(command=lambda argframe=argframe, cmd=cmd, button_prev=button_prev, button_next=button_next, e_list=e_list: prevArg(argframe, cmd,  button_prev, button_next, e_list))
        button_prev.grid_remove()
        button_prev.grid(column=curr-1, sticky=E)   

        button_next.configure(command=lambda argframe=argframe, cmd=cmd, button_prev=button_prev, button_next=button_next, e_list=e_list: nextArg(argframe, cmd, button_prev, button_next, e_list))
        button_next.grid_remove()
        button_next.grid(column=curr, sticky=W) 
        

        Grid.columnconfigure(argframe, curr-1, weight=0)
        Grid.columnconfigure(argframe, curr, weight=0)

        print("-: {}".format(curr-1))
        print("+: {}".format(curr))


def newCommandFrame(subroot, i):
    global root
    global  state

    s = "CMD_{}".format(i)
    cmd_frame = LabelFrame(subroot, name=s.lower(), text = s)
    lbl, e, b = labeledEntry(cmd_frame, "CMD", "cmd_{}_shell".format(i), "", "CMD")
    lbl.grid(row=0, column=0, sticky =E+W)
    e.grid(row=0, column=2, sticky=E+W)
    e.grid_remove()
    b.grid(row=0, column=3)

    state['config_vals']["CMD_{}_SHELL".format(i)] = e


    #argframe
    argframe = Frame(cmd_frame)
    state['config_vals']['cmd_{}_argframe'.format(i)] = argframe
    argframe.grid(row=0, column=2, sticky=E+W)

    Grid.columnconfigure(cmd_frame, 0 , weight=1)
    Grid.columnconfigure(cmd_frame, 1 , weight=1)
    Grid.columnconfigure(cmd_frame, 2 , weight=8)
    
    Grid.rowconfigure(cmd_frame, 0 , weight=1)


    Grid.rowconfigure(argframe, 0, weight=1)
    Grid.columnconfigure(argframe, 0, weight=1)


    sv = StringVar()
    sv.set("arg0")
    state['config_vals']['CMD_{}_ARG_{}'.format(i, 0)] = sv
    e = Entry(argframe, textvariable=sv)
    e.grid(row=0, column=0, sticky=E+W) 
    e_list = [e]
    b_prev = Button(argframe, text="-")
    b_next = Button(argframe, text="+")

    b_prev.configure(command=lambda argframe=argframe, b_prev=b_prev, b_next=b_next, e_list=e_list: prevArg(argframe, i, b_prev, b_next, e_list))
    b_prev.grid(row=0, column=1, sticky=E)

    b_next.configure(command=lambda argframe=argframe, i=i, b_prev=b_prev, b_next=b_next, e_list=e_list: nextArg(argframe, i, b_prev, b_next, e_list))
    b_next.grid(row=0, column=2, sticky=W)
    
    
    sv = StringVar()
    state['config_vals']['SHELL_{}'.format(i)] = sv
    
    sv.trace('w', lambda *args, i=i: changeShellMode(i))

    
    shell_frame = LabelFrame(cmd_frame, text = "SHELL")
    shell_frame.grid(row=0, column=1, sticky=E+W)

    combobox = OptionMenu(shell_frame, sv, *{'TRUE', 'FALSE'})
    sv.set("FALSE")
    combobox.grid(sticky=N+S+E+W)
    Grid.columnconfigure(shell_frame, 0, weight=1)  
    
    b = Button(shell_frame, text="?", command=lambda n="SHELL": helpBox(n))
    
    b.grid(row=0, column=1)




    #labeledWidget(root, label_text, help_name):


    #other settings
    other_frame = Frame(cmd_frame)

    frame = LabelFrame(other_frame, text="ONFAIL")

    b = Button(shell_frame, text="?", command=lambda n="SHELL": helpBox(n))
    b.grid(row=0, column=1, sticky=E+W)
    
    sv = StringVar()
    state['config_vals']['ONFAIL_{}'.format(i)] = sv
        
    combobox = OptionMenu(frame, sv, *{'FAIL', 'IGNORE', 'RESCHEDULE', 'SLEEP'})
    combobox.grid(row=0, column=0, sticky=E+W)
    sv.set('FAIL')

    b = Button(frame, text="?", command=lambda n="ONFAIL": helpBox(n))
    b.grid(row=0, column=1)


    frame.grid(row=0, column=0, sticky=E+W, padx=(100,0))   

    #Grid.rowconfigure(frame, 0, weight=1)
    Grid.columnconfigure(frame, 0, weight=1)
    #Grid.columnconfigure(frame, 1, weight=1)
    

    frame_right = LabelFrame(other_frame, text="TIMEOUT")
    #lbl, e, desc = labeledSpinbox(reschedule_frame, field, s, 0, 1e7, defaults[i], field) 
    #lbl, sp, b = labeledSpinbox(frame, "TIMEOUT_{}".format(i), "TIMEOUT", 0, 1e7, 0, "TIMEOUT")
    iv = IntVar()
    state['config_vals']['TIMEOUT_{}'.format(i)] = iv
        
    spinbox = Spinbox(frame_right , textvariable=iv, from_=0, to=1e7, width=6)

    iv.set("0") 
    spinbox.grid(row=0, column=0, sticky=E+W)
    
    b = Button(frame_right, text="?", command=lambda n="TIMEOUT": helpBox(n))
    b.grid(row=0, column=1)

    
    #Grid.columnconfigure(frame, 2, weight=0)
    #Grid.columnconfigure(frame, 6, weight=0)


    #Grid.rowconfigure(cmd_frame, 0, weight=1)
    #Grid.rowconfigure(cmd_frame, 1, weight=1)
    
    frame_right.grid(row=0, column=1, sticky=E+W, padx=(0, 100))    
    
    #Grid.rowconfigure(frame_right, 0, weight=1)
    Grid.columnconfigure(frame_right, 0, weight=1)
    #Grid.columnconfigure(frame_right, 1, weight=1)
    
    

    for j in range(2):
        Grid.columnconfigure(other_frame, j, weight=1)

    other_frame.grid(row=1, column=0, columnspan=4, sticky=E+W)
    Grid.rowconfigure(other_frame, 0, weight=1)

    
    Grid.rowconfigure(cmd_frame, 0, weight=0)
    Grid.rowconfigure(cmd_frame, 1, weight=0)
    return cmd_frame



def delCmd(commands_frame, b_del, b_add, f_list):
    curr = len(f_list)
    if curr > 1:
        f_list.pop().grid_forget()
        
        del state['config_vals']['CMD_{}_SHELL'.format(curr)]
        b_del.configure(command=lambda commands_frame=commands_frame, b_del=b_del, b_add=b_add, f_list=f_list: delCmd(commands_frame, b_del, b_add, f_list))
        b_add.configure(command=lambda commands_frame=commands_frame, b_del=b_del, b_add=b_add, f_list=f_list: addCmd(commands_frame, b_del, b_add, f_list))
        
        b_del.grid(row=curr-1)
        b_add.grid(row=curr)

def addCmd(commands_frame, b_del, b_add, f_list):
    curr = len(f_list)
    cmd_frame = newCommandFrame(commands_frame, curr+1)

    cmd_frame.grid(row=curr, column=0, sticky=N+S+E+W)

    f_list.append(cmd_frame)
    
    b_del.configure(command=lambda commands_frame=commands_frame, b_del=b_del, b_add=b_add, f_list=f_list: delCmd(commands_frame, b_del, b_add, f_list))
    b_add.configure(command=lambda commands_frame=commands_frame, b_del=b_del, b_add=b_add, f_list=f_list: addCmd(commands_frame, b_del, b_add, f_list))
    
    b_del.grid(row=curr+1)
    b_add.grid(row=curr+2)



def configSaveAs():
    global state
    global root

    d = state['config_vals']

    lines = []  
    
    lines.append("//Commands")


    i = 1
    while True:
        k = "CMD_{}_SHELL".format(i)
        if k in d:
            shell=d['SHELL_{}'.format(i)].get()
            if shell == "TRUE":
                lines.append("{}={}".format("CMD_{}".format(i), d[k].get()))
            else:
                args = []
                j = 0
                while True:
                    k = "CMD_{}_ARG_{}".format(i, j)
                    if k in  d:
                        args.append(d[k].get()) 
                        j = j + 1
                    else:
                        break
                lines.append("{}={}".format("CMD_{}".format(i), d['DELIM'].get().join(args)))
                
    

            for s in ['SHELL', 'ONFAIL', 'TIMEOUT']:
                k = "{}_{}".format(s, i)
                lines.append("{}={}".format(k, d[k].get()))
            
            lines.append("DELIM_{}={}".format(i, d['DELIM'].get()))
            lines.append("")    
            i = i + 1
        else:
            break

    lines.append("")
    
    lines.append("//Placeholders")

    for s in ['TARGET', 'STDOUT', 'STDERR', 'RET', 'TMP']:
        k = "{}_PLACEHOLDER".format(s)
        lines.append("{}={}".format(k, d[k].get()))

    for i in range(2):
        lines.append("")
    lines.append("//On Fail Settings")

    for s in ['RESCHEDULE', 'SLEEP']:
        for t in ['MAX', 'TTL', 'DELAY']:
    
            k = "{}_{}".format(s, t)
            if k in d:
                lines.append("{}={}".format(k, d[k].get()))

    for i in range(2):
        lines.append("")
    lines.append("//Other / General Settings")


    for  k in ['MAX_RUNNING', 'REFRESH_DELAY',  'DEFAULT_WIDTH', 'DEFAULT_HEIGHT', 'DEFAULT_COLUMN_WIDTH', 'GUI_THREADS']:
        lines.append("{}={}".format(k, d[k].get()))


    s = "\n".join(lines)
    print(s)
    saveAs(s.encode(), state['config_editor'])
    

def createConfigEditor():
    global root
    global state
    if state['config_editor']:
        state['config_editor'].deiconify()
        state['config_editor'].grab_set()
    else:
        config_editor = Toplevel(root)
        config_editor.grid()
        state['config_editor'] = config_editor
        config_editor.title("Executor.py - Configurator v1.0")
        config_editor.grab_set()    
                
        Button(config_editor, text="Save As...", command=configSaveAs).grid(row=0, column=0, sticky=W)

        commands_frame = LabelFrame(config_editor, text="Commands")
        commands_frame.grid(row=1, column=0, columnspan=3, sticky=N+S+E+W)
        
        cmd_1 = newCommandFrame(commands_frame, 1)
        cmd_1.grid(row=0, column=0, sticky=N+S+E+W)

        #Grid.rowconfigure(commands_frame, 0, weight=1)
        Grid.columnconfigure(commands_frame, 0, weight=1)


        b_del = Button(commands_frame, text="Delete Command")
        b_add = Button(commands_frame, text="Add Command")
        
        b_del.configure(command=lambda commands_frame=commands_frame, b_del=b_del, b_add=b_add, f_list=[cmd_1]: delCmd(commands_frame, b_del, b_add, f_list))
        b_add.configure(command=lambda commands_frame=commands_frame, b_del=b_del, b_add=b_add, f_list=[cmd_1]: addCmd(commands_frame, b_del, b_add, f_list))
        
        b_del.grid(row=1, column=0, sticky=N+S+E+W, pady=(20,0))
        b_add.grid(row=2, column=0, sticky=N+S+E+W, pady=(0,20))


        placeholders_frame = LabelFrame(config_editor, name="placeholders_frame", text="Placeholders")
        placeholders_frame.grid(row=2, column=0, rowspan=2, sticky=E+W)

        sleep_frame = LabelFrame(config_editor, text="Sleep Settings")
        sleep_frame.grid(row=3, column=1, sticky=E+W, pady=10)
        
        general_frame = LabelFrame(config_editor, text="General Settings")
        general_frame.grid(row=2, column=2, rowspan=2, sticky=E+W)
            
        for i, field in enumerate(['TARGET', 'STDOUT', 'STDERR', 'RET', 'TMP']):
            s = "{}_PLACEHOLDER".format(field)
            d = state['help'][s]

            lbl, e, b = labeledEntry(placeholders_frame, s, s, "{{{}}}".format(field.lower()), s) 
            lbl.grid(row=i, column=0,sticky=N+S+E+W)
            e.grid(row=i, column=1,sticky=N+S+E+W)
            b.grid(row=i, column=2, sticky=N+S+E+W) 
            
            Grid.rowconfigure(placeholders_frame,i, weight=1)           

        Grid.columnconfigure(placeholders_frame, 1, weight=1)
        


        reschedule_frame = LabelFrame(config_editor, text="Reschedule Settings")
        reschedule_frame.grid(row=2, column=1, sticky=E+W, pady=10)
    
        defaults = [2, 0, 300]
        for i, field in enumerate(['RESCHEDULE_MAX', 'RESCHEDULE_TTL', 'RESCHEDULE_DELAY']):
        
            lbl, e, desc = labeledSpinbox(reschedule_frame, field, field, 0, 1e7, defaults[i], field) 
            lbl.grid(row=i, column=0,sticky=N+S+E+W)
            e.grid(row=i, column=1,sticky=N+S+E+W)
            desc.grid(row=i, column=2, sticky=N+S+E+W)  
    
            Grid.rowconfigure(reschedule_frame,i, weight=1)         

        defaults = [2, 120]
        for i, field in enumerate(['SLEEP_MAX', 'SLEEP_DELAY']):
        
            lbl, e, desc = labeledSpinbox(sleep_frame, field, field, 0, 1e7, defaults[i], field) 
            lbl.grid(row=i, column=0,sticky=N+S+E+W)
            e.grid(row=i, column=1,sticky=N+S+E+W)
            desc.grid(row=i, column=2, sticky=N+S+E+W)  

            Grid.rowconfigure(sleep_frame,i, weight=1)          

        defaults = [10, 250, 1024, 600, 100, 8]
        for i, field in enumerate(['MAX_RUNNING', 'REFRESH_DELAY', 'DEFAULT_WIDTH','DEFAULT_HEIGHT', 'DEFAULT_COLUMN_WIDTH', 'GUI_THREADS']):
        
            lbl, e, desc = labeledSpinbox(general_frame, field, field, 0, 1e6, defaults[i], field) 
            lbl.grid(row=i, column=0,sticky=N+S+E+W)
            e.grid(row=i, column=1,sticky=N+S+E+W)
            desc.grid(row=i, column=2, sticky=N+S+E+W)  

            Grid.rowconfigure(general_frame,i,  weight=1)           


        Grid.columnconfigure(placeholders_frame, 1, weight=1)
        Grid.columnconfigure(reschedule_frame, 1, weight=1)
        Grid.columnconfigure(sleep_frame, 1, weight=1)
        Grid.columnconfigure(general_frame, 1, weight=1)



        Grid.rowconfigure(config_editor, 1, weight=1)

        for i in range(3):
            Grid.columnconfigure(config_editor, i, weight=1)

        sv  = StringVar()
        state['config_vals']['DELIM']  = sv
        sv.set("{!-DELIM-!}")
        

        #config_editor.geometry('%dx%d+%d+%d' % (800, 600, 2000, 2000))
        config_editor.protocol("WM_DELETE_WINDOW", editorClose)
        


def attachConfigFrame(root):
    global script_dir
    config_frame = Frame(root, name="config_frame")
    config_frame.grid(row=0,column=0,sticky=E+W, columnspan=6)

    ini_dir = os.path.join(script_dir, "ini")

    Button(config_frame, text="Config File:", command=lambda:browse(config_entry, ['ini'], initialdir=ini_dir)).grid(row=0,column=0,sticky=W)
    

    config_entry = Entry(config_frame, name="config_entry")
    config_entry.insert(END, os.path.basename(__file__).rsplit(".py",1)[0]+".ini")
    config_entry.grid(row=0,column=2,sticky=E+W,padx=8)

    Button(config_frame, text="+", command=createConfigEditor).grid(row=0,column=1, sticky=W)


    Button(config_frame, text="Targets File:",command=lambda:browse(targets_entry, ['list', 'range'], initialdir=os.getcwd())).grid(row=0,column=3,sticky=W)
    targets_entry = Entry(config_frame, name="targets_entry")
    
    targets_entry.insert(END, os.path.join(os.getcwd(), "hosts.list"))
    targets_entry.grid(row=0,column=4, sticky=E+W, padx=8)


    #for c in range(4):
    #   Grid.columnconfigure(config_frame,c,weight=c%2)
    for c in [2, 4]:
        Grid.columnconfigure(config_frame,c,weight=1)
    for c in [0, 1, 3]:
        Grid.columnconfigure(config_frame,c,weight=0)
    Grid.rowconfigure(config_frame,0,weight=1)

def attachManagementFrame(root):
    management_frame = Frame(root, name='management_frame')
    management_frame.grid(row=1,column=0,sticky=N+S+E+W, columnspan=6)



    Label(management_frame, text="Max Running Jobs:").grid(row=0,column=0,sticky=N+S+W)

    spinbox = Spinbox(management_frame, name="max_running_spinbox", from_=0, to=0, width=4)
    spinbox.grid(row=0,column=1,padx=16, sticky=N+S+W)
    
    button_frame = Frame(management_frame)
    button_frame.grid(row=0,column=2,sticky=N+S+E+W)
    Grid.rowconfigure(button_frame,0,weight=1)
    Grid.rowconfigure(button_frame,1,weight=1)

    button_info = [('Load',load), ('Launch',lambda:launch(button_frame))]
    for c in range(2):
        Button(button_frame, text=button_info[c][0], name=button_info[c][0].lower(),
            command=button_info[c][1], width=10).grid(row=0, rowspan=2,column=c, sticky=N+S+E+W
        )
        
    Grid.columnconfigure(button_frame,c,weight=1)
    button_info =   [('Cancel All', cancelAllJobs),('Kill All', killAllJobs), ('Delete All',deleteAllJobs),
             ('Cancel Selected', cancelSelectedJobs), ('Kill Selected',killSelectedJobs), ('Delete Selected', deleteSelectedJobs)
            ]
    for i in range(6):  
        Button(button_frame, text=button_info[i][0], command=button_info[i][1], width=10).grid(row=i//3,column=2+(i%3), sticky=N+S+E+W)
        Grid.columnconfigure(button_frame,2+(i%3),weight=1)
    Grid.rowconfigure(management_frame,0,weight=1)
    Grid.columnconfigure(management_frame,0,weight=1)
    Grid.columnconfigure(management_frame,1,weight=0)
    Grid.columnconfigure(management_frame,2,weight=4)

def reloadJobFrame(root, j):
    global settings
    job_frame = root.nametowidget("main_panel.job_frame")
    for w in job_frame.winfo_children():
        w.destroy()

    if j in jobs:   
        try:
            attachJobFrame(root, jobs[j])
            return
        except Exception:
            print("Inspect Job failed; job may have been deleted")
            pass
    
    attachJobFrame(root, None)
    
def attachJobFrame(root, job=None):

    job_frame = None    
    if not job:
        job_frame = Frame(root, name="job_frame")
    else:
        job_frame = root.nametowidget("main_panel.job_frame")
    
    attempt_notebook = Notebook(job_frame, name="attempt_notebook")
    attempt_notebook.grid(row=3, column=0, columnspan=2, sticky=N+S+E+W)

    if not job:
        Label(job_frame, name="job_label", text="Job Details").grid(row=0,column=0)
        Grid.columnconfigure(job_frame, 0, weight=1)
        Grid.rowconfigure(job_frame, 3, weight=1)   
                
    else:
        stats = job.getStats()
        #print(stats)

        Label(job_frame, name="job_label", text="Job Details:\n{}".format(job.getTarget())).grid(row=0,column=0, sticky=N+S+E+W)
        
        # could reuse button frame if needed for performance
        button_frame = Frame(job_frame)
        button_frame.grid(row=0, column=1,sticky=N+S+E+W)
        Button(button_frame, text=u"\u21bb", command=lambda:reloadJobFrame(root, job.getTarget())).grid(row=1, column=0, sticky=N+S+E+W)
        Button(button_frame, text=u"Requeue", command=lambda:requeueJob(job.getTarget())).grid(row=1, column=1, sticky=N+S+E+W)
        Button(button_frame, text="Cancel", command=lambda:killJob(job.getTarget(), polite=True)).grid(row=0, column=0, sticky = N+S+E+W)
        Button(button_frame, text="Kill", command=lambda:killJob(job.getTarget(), polite=False)).grid(row=0, column=1, sticky = N+S+E+W)
        


        Label(job_frame, text="Status: {}".format(job.getStatus())).grid(row=1,column=0)
        
        t = time.strftime("%H:%M:%S", time.gmtime(job.getElapsed()))
    
        Label(job_frame, text="Elapsed: {}".format(t)).grid(row=1,column=1)
        times = job.getTimes()
        times = [time.strftime("%H:%M:%S", time.gmtime(t)) if t else "N/A" for t in times]
        Label(job_frame, text="Started: {}".format(times[0])).grid(row=2,column=0)
        Label(job_frame, text="Stopped: {}".format(times[1])).grid(row=2,column=1)
        
        for attempt_num, attempt_data in stats.items():
            #print("Attempt: {}".format(attempt_num))
            #print("Data: {}".format(attempt_data))
            notebook = Notebook(attempt_notebook, name="stage_notebook_{}".format(attempt_num))
            #notebook.grid(row=1,column=0, sticky=N+S+E+W)
            for stage_num, stage_data in attempt_data.items():      
                #print("Stage: {}".format(stage_num))
                #print("Data: {}".format(stage_data))
                if stage_data:
                    messages = Frame(notebook)
                    Label(messages, text="Return Code: {}".format(stage_data['ret_code'])).grid(row=0, column=0, sticky=W)
                    for row, msg, lbl in [(1,'msg_out', "STDOUT"), (2,'msg_err', "STDERR")]:
                        lines = stage_data[msg].splitlines()
                        width=1
                        height=1
                        if lines:
                            width = min(len(max(lines, key=len)) + 2, 800)          
                            height = min(len(lines) + 1, 100)
                        #print("Dims: {}x{}".format(width, height))

                        lbf = LabelFrame(messages, text=lbl)
                        lbf.grid(row=row, column=0, sticky = N+S+E+W)
                        if stage_data[msg]:     
                            Button(lbf, text="\u279a", command=lambda s=stage_data[msg]: saveAs(s)).grid(row=0, column=0, sticky=W+N+S)
                            Button(lbf, text="\u2702", command=lambda s=stage_data[msg]: copyToClipboard(s)).grid(row=1, column=0, sticky=W+N+S)
                            
                            msg_scrolledtext = ScrolledText(lbf, width=width, height=height)
                            
                            msg_scrolledtext.insert(END, stage_data[msg])
                            msg_scrolledtext.config(state="disabled")
                        
                            msg_scrolledtext.grid(row=0,column=1,rowspan=2, sticky=N+S+E+W)
                            msg_scrolledtext.bind("<Control-c>", lambda event: copySelectedText(msg_scrolledtext), add="+") 
                            msg_scrolledtext.bind("<Button-1>",lambda event, tb=msg_scrolledtext: tb.focus_set() , add="+")
                            msg_scrolledtext.bind("<Control-a>",lambda *args, tb=msg_scrolledtext: selectAllText(tb), add="+")
                        else:
                            Label(lbf, text="N/A").grid(row=0, column=0, sticky=N+S+E+W)
    
                    notebook.add(messages,text="Stage {}".format(stage_num), sticky=N+S+E+W)
                    try:
                        notebook.select(notebook.tabs()[-1])
                    except Exception:
                        pass    
            attempt_notebook.add(notebook, text="Attempt {}".format(attempt_num), sticky=N+S+E+W)
            try:
                attempt_notebook.select(attempt_notebook.tabs()[-1])
            except Exception:
                pass    

    return job_frame



def attachMainPanel(root):
    main_panel = PanedWindow(root, name="main_panel", orient=HORIZONTAL, relief='groove', sashrelief='groove', sashpad=4)
    main_panel.grid(row=2, column=0, columnspan=6,sticky=N+S+E+W)
    #Grid.rowconfigure(main_panel, 0, weight=1)
    #Grid.columnconfigure(main_panel,0, weight=1)
    #Grid.columnconfigure(main_panel,1, weight=1)
    #main_panel.config(width)
    return main_panel

def attachStatusFrame(root):
    global state

    DEFAULT_COLUMN_WIDTH=100

    #status_frame = Frame(root, name="status_frame")
    
    status_frame = PanedWindow(root, name="status_frame", orient=HORIZONTAL, relief='groove', sashrelief='groove', sashpad=4)
    #status_frame.grid(row=0, column=1, sticky=N+S+E+W)
    labels = ['Queued:{}','Running:{}','Finished:{}','Failed:{}','Rescheduled:{}']

    for f in range(5):
        name = labels[f].split(':')[0].lower()
        frame = Frame(status_frame,name=name+"_frame")
        #frame.grid(row=0,column=f,sticky=N+S+E+W)
        
        heading = Frame(frame, name="heading_frame")
        heading.grid(row=0,column=0, columnspan=2, sticky=E+W)
    
        
    
        #lbl = Label(heading, name=name+"_label", text=labels[f].format("N/A"))
        lbl = Button(heading, name=name+"_label", text=labels[f].format("N/A"), command=lambda n=name: toggleSelection(n))
        lbl.grid(row=0,column=0,sticky=W+E)
        state['label'][name] = lbl

        scrollbar = Scrollbar(frame)
        scrollbar.grid(row=1,column=1, sticky=N+S+W)
        
        base_name = "status_frame.{0}_frame.{0}_listbox"
        listbox = None
        if f == 1:  
            listbox = Treeview(frame, name=name+"_listbox", columns=["target","progress"], selectmode=EXTENDED)
            listbox.heading("progress", text="Progress", command=lambda _n=name: sortTreeviewColumn(root, base_name.format(_n), 'progress', False))
        
        
            listbox.column("progress", anchor=CENTER, width=DEFAULT_COLUMN_WIDTH)

            #add more as needed
            colors = ['light goldenrod', 'cyan', 'orchid1', 'pale green', 'cornflower blue', 'coral', 'turquoise1', 'gold3', 'OliveDrab1', 'purple1', 'light sea green']
            for i in range(len(colors)):
                listbox.tag_configure("stage_{}".format(i+1), background=colors[i])
            listbox.tag_configure("stage_sleep", background='gray75')

        else:
            listbox = Treeview(frame, name=name+"_listbox", columns=["target"], selectmode=EXTENDED)

        

        state['listbox'][name] = listbox

        
        listbox['show'] = 'headings'
        listbox.heading("target", text="Target", command=lambda _n=name: sortTreeviewColumn(root, base_name.format(_n), 'target', False))
        listbox.column("target", anchor=CENTER, width=DEFAULT_COLUMN_WIDTH)

    
        #listbox = Listbox(frame,name=name+"_listbox", selectmode=EXTENDED)
        listbox.grid(row=1,column=0, sticky=N+S+E+W)

        #listbox.bind('<<ListboxSelect>>', inspectJob)
        listbox.bind('<<TreeviewSelect>>', inspectJob)
        listbox.bind('<Control-c>', lambda *args, n=name: copySelection(n), add="+")
        listbox.bind('<Control-a>', lambda *args, n=name: selectAll(n), add="+")

        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        Grid.columnconfigure(frame,0,weight=1)
        Grid.columnconfigure(frame,1,weight=0)

        Grid.rowconfigure(frame,0,weight=0)
        Grid.rowconfigure(frame,1,weight=1)
        
        status_frame.add(frame, stretch="always")
        #Grid.columnconfigure(status_frame, f, weight=1)

        heading.columnconfigure(0, weight=1)    
    
        Button(heading, text="\u279a", command=lambda tv=listbox: exportItems(tv)).grid(row=0, column=1, sticky=W+E)        

    #Grid.rowconfigure(status_frame, 0, weight=1)
    return status_frame
def updateMaxRunning(*args):
    global settings
    global root
    global state
    try:
        i = int(root.nametowidget("management_frame.max_running_spinbox").get())
        state['changed_max_running']=True
        if i >= 0:
            if settings:
                settings['MAX_RUNNING'] = i
                print("MAX_RUNNING set to {}".format(i))
        else:
            print("Invalid value for Max Running: must be >= 0")

    except Exception as e:
        print("Invalid value for Max Running - Exception: ")
        print(e)



def killAllJobs(polite=False, move=True):
    global jobs
    global state
    #for n in state['check']:
    #   state['check'][n] = True
    #   state['changed'][n] = True
    for q in ['queued', 'rescheduled', 'rescheduled_ready', 'sleeping', 'sleeping_ready', 'sitrep']:
        state['queue'][q].queue.clear()
    if jobs:
        print("Killing all jobs!")
        state['abort_load'] = True
        for target, job in list(jobs.items()):
            killJob(target, polite=polite, move=move)
        state['abort_load'] = False

    for q in ['queued', 'rescheduled', 'rescheduled_ready', 'sleeping', 'sleeping_ready', 'sitrep']:
        state['queue'][q].queue.clear()

def cancelAllJobs():
    killAllJobs(polite=True, move=False)

def deleteAllJobs():
    global jobs
    global state
    killAllJobs(polite=False, move=False)
    jobs={}
    children={}
    for n in state['selection']:
        state['selection'][n] = []
        state['changed'][n] = True
        listbox = root.nametowidget("main_panel.status_frame.{0}_frame.{0}_listbox".format(n))
        for c in listbox.get_children():
            listbox.delete(c)

def killSelectedJobs(polite=False, move=True):
    global state
    for n, l in state['selection'].items():
        state['check'][n] = True
        state['changed'][n] = True
        for t in l:
            killJob(t, polite=polite, move=move)
def cancelSelectedJobs():
    killSelectedJobs(polite=True, move=False)

def deleteSelectedJobs():
    global jobs
    killSelectedJobs(polite=False, move=False)
    for n in ['queued', 'running', 'finished', 'failed', 'rescheduled']:
        listbox = root.nametowidget("main_panel.status_frame.{0}_frame.{0}_listbox".format(n))
        for c in state['selection'][n]:
            listbox.delete(c)
            try:
                del jobs[c]
            except Exception:
                pass
        state['selection'][n] = []

#def forceLoad():
#    for t in l:
#        killJob(t, polite=False, move=False)


def closeHandler():
    global root
    state['quit'] = True
    killAllJobs()
    root.destroy()
    print("Collecting GUI threads...")

    #wake up all the blocking queues so they can exit
    for n in state['queue']:
        try:
            state['queue'][n].put_nowait((0,random.random(), 'quit'))
            if n == 'sitrep':
                for i in range(NUM_CHECKERS):
                    state['queue'][n].put_nowait((0, random.random(), 'quit'))
                    
        except Exception as e:
            pass
    state['executor'].shutdown()


def initHelp():
    d = {}
    d["TARGET_PLACEHOLDER"] = """
This placeholder will be replaced with a single line from the Target's file.
"""
    d["STDOUT_PLACEHOLDER"] = """
This placeholder will be replaced with the filename of a temporary file.

When the command using this placeholder is executed, that temporary file will contain what the previous command in the chain wrote to STDOUT (standard output).
"""
    d["STDERR_PLACEHOLDER"] = """
This placeholder will be replaced with the filename of a temporary file.

When the command using this placeholder is executed, that temporary file will contain what the previous command in the chain wrote to STDERR (standard error).
"""
    d["RET_PLACEHOLDER"] = """
This placeholder will be replaced with the return value of the previous command in the chain.
"""
    d["TMP_PLACEHOLDER"] = """
This placeholder will be replaced with the filename of a temporary file. This file will persist for the duration of the current execution chain.

It can be used to pass temporary output between commands in the chain, or to allow a command to communicate with itself between attempts if using ONFAIL=>SLEEP.

Note that, as with STDOUT and STDERR, the termination of the execution chain (either by finishing, failing, or being rescheduled) will cause all associated temp files to be deleted.

If persistent storage is needed, the commands in the chain should take care of it (a simple copy command should usually suffice).

"""
    d['RESCHEDULE_MAX'] = """
Used when ONFAIL is set to RESCHEDULE and a command failed.

This is the maximum number of times that a job can be retried after failure before it becomes FAILED and no further attempts are made.
"""
    d['RESCHEDULE_TTL'] = """
Used when ONFAIL is set to RESCHEDULE and a command failed.

This is the maximum number of seconds since the beginning of the first attempt of a particular job before the job will no longer request to be rescheduled.

After this Time-To-Live expires, the job will change behavior from ONFAIL->RESCHEDULE to ONFAIL->FAIL.

Note: this does not guarantee anything about the actual time that a job will be attempted. The check is done at the time of failure. If the check passes, the job will be requeued and eventually re-executed, even if there is not an open execution slot for a very long time.

If the value is too low, the job may never be rescheduled (as the TTL will have expired before the end of the first attempt).

If set to 0 (the default), this setting is ignored.
"""

    d['RESCHEDULE_DELAY'] = """
Used when ONFAIL is set to RESCHEDULE and a command failed.

This is the minimum number of seconds since the failure of a command before the entire job can be re-attempted.

After this time has passed, the job becomes elibile for re-execution and has the same priority as a QUEUED job (and a lower priority than SLEEPING jobs).
"""


    d['SLEEP_MAX'] = """
Used when ONFAIL is set to SLEEP and a command failed.

This is the maximum number of times that a command can be retried after failure before the job becomes FAILED and no further attempts are made.
"""

    d['SLEEP_DELAY'] = """
Used when ONFAIL is set to SLEEP and a command failed.

This is the minimum number of seconds since the failure of a command before the command in question can be re-attempted.

After this time has passed, the job becomes elibile for re-execution with the highest priority (higher than QUEUED or RESCHEDULED).
"""
    d['MAX_RUNNING'] = """
The number of jobs to execute simultaneously.

This can be adjusted at runtime, but this value will be applied when settings are loaded. A sleeping job does not count against MAX_RUNNING until it is resumed.
"""

    d['DEFAULT_WIDTH'] = """
The default width of the main window.

[TODOi - not implemented]
"""

    d['DEFAULT_HEIGHT'] = """
The default height of the main window.

[TODO]
"""
    d['DEFAULT_COLUMN_WIDTH'] = """
The default width of the Queued, Running / Sleeping, Finsihed, Failed, and Rescheduled columns.

[TODO - not implemented]
"""
    d['GUI_THREADS'] = """
The number of threads to spawn for GUI management.

Note: if this value is too low (~5), Executor.py will not function correctly. Also, more is not always better.

[TODO - not implemented]
"""
    
    d['REFRESH_DELAY'] = """
The number of MILLISECONDS between display updates.

If this number is too high, the GUI will suddenly and regularly stop being responsive. If this number is too low, the GUI may be perpetually unresponsive, as it cannot handle events and update GUI widgets simultaneously.

"""


    d['SHELL'] = """
The execution mode of the command:

If TRUE, the command is passed as a single string to the default system shell. This means that all shell syntax rules apply (whitespace, special characters, etc.) 

TRUE must be used if the command needs to use shell-specific pipes, I/O redirection, shell only commands, or is a command sequence.

If FALSE, the command is invoked directly by the system. You are responsible for placing each argument in the appriate slot (see + and - buttons). Whitespace, shell metacharacters, etc. will be passed as literals to the executable binary / script in the arg0 slot.

FALSE should be used whenever possible, as it is more efficient (no intermediary shell). It can be particularly useful when the command contains whitespaces or special characters in the argument, and quoting / escaping these characters is no longer necessary.

"""

    d['ONFAIL'] = """
The action to take if this command fails (returns a non-zero exit code).

FAIL: the entire job will be marked failed - no further execution will occur.

IGNORE: the job will continue as if the return code had been 0 - the next command in the sequence will be executed.

RESCHEDULE: this attempt of the job will stop and all resources (including temporary files) will be released. When ready (as determined by the Reschedule Settings), the job will become eligible to be restarted. This will create an additional attempt that begins at the very first command. A Rescheudled job that is ready has the same priority as a Queued job.

SLEEP: the job will be suspended without releasing any temporary files. When ready (as determined by  the Sleep Settings), the job will become eligible to be resumed. This will create an additional attempt that begins with this command (the command that failed). Sleeping jobs do not count against MAX_RUNNING and are woken (when ready) with the highest priority (higher than Queued or Rescheduled jobs. 

"""


    d['TIMEOUT'] = """
The maximum amount of seconds to wait for this command to complete before making a best-effort attempt to kill it.

A setting of 0 indicates that the job should wait indefinitely for the command to complete. Otherwise, if the command exceeds this time, it will be killed and this command's ONFAIL behavior will be invoked.

Use with caution - killing processes can be dangerous to system integrity, especially if the command is performing a critical operation. Only use when the command is safe to kill and that taking longer than expected indicates a failure.

"""

    d['CMD'] = """
A command is a "Stage" of a Job. A Job is created for each Target (i.e. line in the Targets file). A Job can contain an arbitrary sequence of Commands / Stages.

"""


    

    return d


def initState():
    d = {}
    d['stats'] = {'elapsed':{}, 'mean':0.0, 'std_dev':0.0, 'mode':'indeterminate'}
    for s in ['selection', 'listbox', 'check', 'changed', 'label', 'queue']:
        d[s] = {}
    for n in ['queued', 'running', 'rescheduled', 'finished', 'failed']:
        d['selection'][n] = []
        d['listbox'][n] = None
        d['label'][n] = None
        d['check'][n] = False
        d['changed'][n] = False
    
    for n in ['queued', 'rescheduled', 'rescheduled_ready', 'sleeping', 'sleeping_ready']:
        d['queue'][n] = queue.Queue()

    d['queue']['mgmt'] = Manager().Queue()

    d['queue']['move'] = queue.Queue(4096)
    d['queue']['sitrep'] = queue.PriorityQueue(4096)

    d['update_dict'] = {}

    d['running_dict'] = {}
    d['executor'] = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    d['launched'] = False
    d['quit'] = False
    d['abort_load'] = False
    d['config_editor'] = None
    d['config_vals'] = {}

    d['help'] = initHelp()
    d['changed_max_running']=False
    #d['check']['queued'] = True
    return d

if __name__ =="__main__":
    global settings
    global jobs
    global root
    global manager
    global children
    global state
    global script_dir

    script_dir = os.path.dirname(os.path.realpath(__file__))

    jobs = None
    manager = None
    settings = None
    
    children = {}

    


    DEFAULT_WIDTH=1024
    DEFAULT_HEIGHT=600

    #Number of threads dedicated to GUI
    #~5+NUM_CHECKERS is the absolute minimum or the GUI cannot function 
    #(most of the threads are dedicated to a particular task)
    MAX_WORKERS=8

    # Must be at least 1 and no more than MAX_WORKERS-5
    NUM_CHECKERS=2


    state=initState()
    # Draw GUI

    root=Tk()

    root.title("Executor.py v1.0")
    
    root.protocol("WM_DELETE_WINDOW", closeHandler)
    #for r in range(3):
    #   Grid.rowconfigure(root,r,weight=0)

    Grid.rowconfigure(root,0,weight=0)
    Grid.rowconfigure(root,1,weight=1)
    Grid.rowconfigure(root,2,weight=50)

    for c in range(6):
        Grid.columnconfigure(root,c,weight=1)

    attachConfigFrame(root)
    attachManagementFrame(root)
    main_panel = attachMainPanel(root)

    
    main_panel.add(attachJobFrame(main_panel), stretch="first", minsize=DEFAULT_WIDTH/6)
    main_panel.add(attachStatusFrame(main_panel), stretch="first")

    #main_panel.nametowidget(main_panel.panes()[0]).config(width=500)   

    w = max(root.winfo_reqwidth(), DEFAULT_WIDTH)
    h = max(root.winfo_reqheight(), DEFAULT_HEIGHT)
    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (h/2)
    y = (hs/2) - (w/2)

    # set the dimensions of the screen 
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    #root.after(0, checkProgress)

    #root.after(0, moveAll)
    #root.after(0, updateAll)

    #root.after(0, updateListboxWorker)
    
    
    for n in ['rescheduled', 'sleeping']:
        state['executor'].submit(queueConsumer, n)

    
    state['executor'].submit(queueConsumer, "mgmt")

    # IF DECREASING MAX_WORKERS, DECREASE THIS AS WELL
    for i in range(NUM_CHECKERS):
        state['executor'].submit(queueConsumer, 'sitrep')

    #for i in range(2):
    #   state['executor'].submit(queueConsumer, 'sitrep')
 
    state['executor'].submit(checkFree)
    #root.after(5000, checkFree)

    #for n in ['move']:
    root.after(0, lambda: guiQueueConsumer('move'))

    root.after(0, updateItems)
    #root.after(0, lambda: updateCounts(['queued', 'running', 'finished', 'failed', 'rescheduled']))

    root.after(0, lambda: onIdle(lambda: updateCounts(['queued', 'running', 'finished', 'failed', 'rescheduled']) ))

    root.after(0, flushIdle)    


    #Toplevel(root).title("Hello there")
    #root.iconify()

    mainloop()





