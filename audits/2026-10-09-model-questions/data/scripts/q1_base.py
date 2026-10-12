import sys; sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
from harness import *
t, r = run(draws=int(sys.argv[1]) if len(sys.argv)>1 else 500)
print('secs', r._secs)
show(summary(r), 'baseline live 2026')
