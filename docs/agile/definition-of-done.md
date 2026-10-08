# Quality-focused Definition of Done

A change is done when the following applicable conditions are met:

- requirement and acceptance criteria are clear, versioned, and traceable;
- risk and interoperability impact have been reviewed;
- code, configuration, schema, and test changes are peer-reviewable;
- suitable unit or component automation exists for changed logic;
- live integration evidence exists for changed service boundaries;
- negative, error-handling, and recovery paths are covered according to risk;
- fixed defects have exact retest and root-cause-based regression evidence;
- no Critical or High issue remains without explicit disposition;
- logs and reports avoid credentials and uncontrolled payload data;
- documentation, runbooks, and known limitations are updated;
- CI quality gates pass on the target commit;
- release, migration, monitoring, and rollback effects are understood.

A test that is skipped, blocked, or never selected is not silently counted as passed. Any exception to this definition is recorded with owner, rationale, containment, and review date.
