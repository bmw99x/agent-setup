# Tests for login lockout

Staff portal logins go through `authenticate` in `/app/app/auth/login.py`, which locks an account after repeated failed attempts (the rules are in its docstring). There are no tests for it, and support keeps asking whether lockouts really lift after 15 minutes.

Add a pytest suite under `/app/tests/` covering the lockout rules. CI has no LDAP server. The failure counts live in a process-wide throttle, so I've seen earlier attempts at tests leak state into each other; make sure each test starts clean and the suite passes in any order, and that nothing has to actually wait 15 minutes. `pytest` from `/app` should pass.
