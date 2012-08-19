from r2.lib.db.thing import Thing


class KarmaAdjustment(Thing):
    @classmethod
    def store(cls, account, sr, amount):
        adjustment = cls(account_id = account._id, sr_id = sr._id, amount = amount)
        adjustment._commit()

