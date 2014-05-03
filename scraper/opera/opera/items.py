from scrapy.item import Item, Field

class SpectacleItem(Item):
    name = Field()
    name_id = Field()
    stype = Field()
    url = Field()
    location = Field()

class ReprItem(Item):
    spectacle = Field()
    date = Field()
    url = Field()
    seats = Field()

class SeatsItem(Item):
    category = Field()
    zones = Field()
    quantity = Field()
    price = Field()
