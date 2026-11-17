"""Run an explicit command with a full log and a process-tree timeout."""
import argparse
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--timeout', required=True, type=float)
    parser.add_argument('--log', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('provide a command and a positive timeout')
    # CreateProcess does not reliably apply PATHEXT to bare names such as sbt.
    # Resolve batch launchers explicitly; preserve argument boundaries and shell=False.
    if os.name == 'nt' and not os.path.dirname(command[0]):
        executable = shutil.which(command[0])
        if executable is None:
            print(f'runner error: executable not found on PATH: {command[0]}', file=sys.stderr)
            return 125
        command[0] = executable
    log = Path(args.log).resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental loss of a previous run's evidence.
    try:
        with log.open('x', encoding='utf-8') as stream:
            kwargs = {'start_new_session': True} if os.name != 'nt' else {
                'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
            process = subprocess.Popen(command, cwd=args.cwd, stdout=stream,
                                       stderr=subprocess.STDOUT, **kwargs)
            try:
                code = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                if os.name == 'nt':
                    killed = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, timeout=20)
                    if killed.returncode and process.poll() is None:
                        raise RuntimeError('taskkill failed to terminate process tree')
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=20)
                stream.write('\n[run_checked] WALLCLOCK TIMEOUT\n')
                code = 124
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'runner error: {error}', file=sys.stderr)
        return 125
    print(f'exit={code} log={log}')
    # This is a command result, not a functional-test verdict.
    return code if code >= 0 else 128 - code


if __name__ == '__main__':
    sys.exit(main())
