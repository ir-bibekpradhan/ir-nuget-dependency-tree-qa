# S20d: staleAssets

Restore and verify the known valid baseline, preserve its evidence, then deliberately staleAssets. This happens before PSE finalization so IR encounters invalid evidence. IR should report the evidence problem or explicitly label reduced confidence; a silently complete, successful tree is a failure. See out/S20d/ for baseline and mutation details.
