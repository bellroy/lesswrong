import pickle

from r2.lib.db.thing import Thing


class PendingJob(Thing):
    @classmethod
    def store(cls, run_at, action, data):
        if data is not None:
            data = pickle.dumps(data)
        adjustment = cls(run_at=run_at, action=action, data=data)
        adjustment._commit()
