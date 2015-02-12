from service import db


class AddressBase(db.Model):
    uprn = db.Column(db.Integer, primary_key=True)
    toid = db.Column(db.String(20))
    udprn = db.Column(db.Integer)
    organisationName = db.Column(db.String(60))
    departmentName = db.Column(db.String(60))
    poBoxNumber = db.Column(db.String(6))
    buildingName = db.Column(db.String(50))
    subBuildingName = db.Column(db.String(30))
    buildingNumber = db.Column(db.Integer)
    dependentThoroughfareName = db.Column(db.String(80))
    thoroughfareName = db.Column(db.String(80))
    postTown = db.Column(db.String(30))
    doubleDependentLocality = db.Column(db.String(35))
    dependentLocality = db.Column(db.String(35))
    postcode = db.Column(db.String(8))
    postcodeType = db.Column(db.String(1))
    positionX = db.Column(db.Float)
    positionY = db.Column(db.Float)
    rpc = db.Column(db.Integer)
    changeType = db.Column(db.String(1))
    startDate = db.Column(db.Date)
    entryDate = db.Column(db.Date)
    lastUpdateDate = db.Column(db.Date)
    primaryClass = db.Column(db.String(1))
    processDate = db.Column(db.Date)


    def __str__(self):
        return '<AddressBase {}>'.format(self.UPRN)
