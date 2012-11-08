# -*- Mode: Python -*-

tasks = []

def schedule (fun, *args):
    tasks.append ((fun, args))

def run():
    while len(tasks):
        fun, args = tasks.pop(0)
        fun (*args)
        
