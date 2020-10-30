import sys

verboseSteps = []
verboseStep = 0

def writeToConsole(verboseValue=None, done: bool=False):
    global verboseStep
    try:
        sys.stdout.write("Verbose: %s ... %s%s" % (verboseSteps[verboseStep], (str(verboseValue) if verboseValue else ""), (" Done" if done else "")))
        sys.stdout.flush()
        sys.stdout.write('\r')
        if done:
            sys.stdout.write('\n')
            verboseStep += 1
            if len(verboseSteps) > verboseStep:
                writeToConsole()
    except IndexError:
        pass

def addVerboseSteps(steps : list):
    global verboseSteps
    verboseSteps += steps

