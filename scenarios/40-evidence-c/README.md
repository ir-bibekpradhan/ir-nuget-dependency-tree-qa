# S20c: missingLock

Restore and verify the known valid baseline, preserve its evidence, then deliberately missingLock. This happens before PSE finalization so IR encounters invalid evidence. IR should report the evidence problem or explicitly label reduced confidence; a silently complete, successful tree is a failure. See out/S20c/ for baseline and mutation details.
