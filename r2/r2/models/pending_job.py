from r2.lib.db.thing import Thing


class PendingJob(Thing):
    @classmethod
    def store(cls, run_at, action, data=None):
        adjustment = cls(run_at=run_at, action=action, data=data)
        adjustment._commit()
