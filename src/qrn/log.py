
log_file = None

def init_log(path):
    global log_file
    log_file = open(path, 'w')

def log(*msgs):
    global log_file
    for m in msgs:
        log_file.write(str(m))
        log_file.write(' ')
    log_file.write('\n')
    log_file.flush()

