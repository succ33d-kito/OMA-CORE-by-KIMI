"""Install an unprivileged user timer for one-shot prospective collection.

Never schedules from Work mode; run explicitly on the user's eligible Linux host.
"""
import argparse,os,shlex,sys
from pathlib import Path

NAME='oma-core-prospective'
CALENDAR='*-*-* *:0/5:02 UTC'

def render(*,repo,python,state,wrapper):
    repo=Path(repo).resolve();python=Path(python).resolve();state=Path(state).expanduser().resolve();wrapper=Path(wrapper).expanduser().resolve()
    script=repo/'scripts/binance_research_collect.py'
    if not script.is_file() or not python.is_file():raise ValueError('repository script and Python must exist')
    shell='#!/bin/sh\nexec '+ ' '.join(shlex.quote(str(x)) for x in [python,script,state/'receipts.db','--raw-dir',state/'raw'])+'\n'
    service=f'''[Unit]\nDescription=OMA-CORE prospective research capture (no trading)\nWants=network-online.target\nAfter=network-online.target\n\n[Service]\nType=oneshot\nEnvironmentFile=-%h/.config/oma-core/prospective.env\nExecStart={wrapper}\nTimeoutStartSec=90\n\n'''
    timer=f'''[Unit]\nDescription=Poll research feed every five minutes after the interval closes\n\n[Timer]\nOnCalendar={CALENDAR}\nAccuracySec=1s\nPersistent=false\nUnit={NAME}.service\n\n[Install]\nWantedBy=timers.target\n'''
    return {'wrapper':shell,'service':service,'timer':timer}

def install(repo,python,state,units,wrapper,*,activate=False):
    paths={'wrapper':Path(wrapper).expanduser(),'service':Path(units).expanduser()/f'{NAME}.service','timer':Path(units).expanduser()/f'{NAME}.timer'}
    content=render(repo=repo,python=python,state=state,wrapper=paths['wrapper'])
    for key,p in paths.items():
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content[key]);p.chmod(0o700 if key=='wrapper' else 0o644)
    if activate:
        import subprocess
        subprocess.run(['systemctl','--user','daemon-reload'],check=True)
        subprocess.run(['systemctl','--user','enable','--now',f'{NAME}.timer'],check=True)
    return paths

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--python',type=Path,default=Path(sys.executable));p.add_argument('--state',type=Path,default=Path.home()/'.local/share/oma-core/prospective');p.add_argument('--units',type=Path,default=Path.home()/'.config/systemd/user');p.add_argument('--wrapper',type=Path,default=Path.home()/'.local/bin/oma-core-prospective-poll');p.add_argument('--activate',action='store_true');p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    if a.dry_run:
        for k,v in render(repo=a.repo,python=a.python,state=a.state,wrapper=a.wrapper).items():print(f'## {k}\n{v}')
    else:
        for k,v in install(a.repo,a.python,a.state,a.units,a.wrapper,activate=a.activate).items():print(k,v)
if __name__=='__main__':main()
