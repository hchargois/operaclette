from opera import config, items
from pymongo import MongoClient
from datetime import datetime

class MongoPipeline(object):
    def open_spider(self, spider):
        client = MongoClient(config.MONGO_URL)
        self.db = client[config.MONGO_DBNAME]

    def process_spectacle(self, spectacle):
        col = self.db.spectacles
        url = spectacle["url"]
        now = datetime.now()
        col.update(
            {"url": url},
            {
                "$set": {
                    "name": spectacle["name"],
                    "name_id": spectacle["name_id"],
                    "type": spectacle["stype"],
                    "location": spectacle["location"],
                    "last_update": now,
                },
                "$setOnInsert": {
                    "insert_date": now,
                },
            },
            upsert=True
        )

    def process_repr(self, r):
        col = self.db.representations
        now = datetime.now()
        spectacle = self.db.spectacles.find_one({"name_id":r["spectacle"]["name_id"]})
        col.update(
            {"spectacle_id": spectacle["_id"], "date": r["date"]},
            {
                "$set": {
                    "url": r["url"],
                    "last_update": now,
                    "seats": map(dict, r["seats"]),
                },
                "$setOnInsert": {
                    "insert_date": now,
                }
            },
            upsert=True
        )

    def consolidate_spectacles(self):
        for spectacle in self.db.spectacles.find():
            prices_available = set()
            dates = []
            for r in self.db.representations.find({"spectacle_id":spectacle["_id"]}):
                dates.append(r["date"])
                for seat in r["seats"]:
                    if seat["quantity"]:
                        prices_available.add(seat["price"])
            dates.sort()
            spectacle["n_representations"] = len(dates)
            if dates:
                spectacle["first_representation"] = dates[0]
                spectacle["last_representation"] = dates[-1]
            else:
                spectacle["first_representation"] = None
                spectacle["last_representation"] = None
            spectacle["prices_available"] = sorted(list(prices_available))
            self.db.spectacles.save(spectacle)

    def process_item(self, item, spider):
        if isinstance(item, items.SpectacleItem):
            self.process_spectacle(item)
        elif isinstance(item, items.ReprItem):
            self.process_repr(item)
        return item

    def close_spider(self, spider):
        self.consolidate_spectacles()
