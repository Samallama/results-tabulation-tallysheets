from app import db
from sqlalchemy.orm import relationship
from orm.enums import AreaTypeEnum, AreaCategoryEnum
from orm.entities import Election
from sqlalchemy.ext.hybrid import hybrid_property
from util import get_paginated_query, get_array


class AreaModel(db.Model):
    __tablename__ = 'area'
    areaId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    areaName = db.Column(db.String(100), nullable=False)
    areaType = db.Column(db.Enum(AreaTypeEnum), nullable=False)
    electionId = db.Column(db.Integer, db.ForeignKey(Election.Model.__table__.c.electionId), nullable=False)
    # parentAreaId = db.Column(db.Integer, db.ForeignKey(areaId), nullable=True)

    election = relationship(Election.Model, foreign_keys=[electionId])
    # parentArea = relationship("AreaModel", remote_side=[areaId])
    # childAreas = relationship("AreaModel", foreign_keys=[parentAreaId])
    # pollingStations = relationship("PollingStationModel")

    # this relationship is used for persistence
    children = relationship("AreaModel", secondary="area_area",
                            primaryjoin="AreaModel.areaId==AreaAreaModel.parentAreaId",
                            secondaryjoin="AreaModel.areaId==AreaAreaModel.childAreaId"
                            )
    parents = relationship("AreaModel", secondary="area_area",
                           primaryjoin="AreaModel.areaId==AreaAreaModel.childAreaId",
                           secondaryjoin="AreaModel.areaId==AreaAreaModel.parentAreaId"
                           )

    def __init__(self, areaName, electionId):
        super(AreaModel, self).__init__(
            areaName=areaName,
            electionId=electionId
        )
        db.session.add(self)
        db.session.commit()

    def add_parent(self, parentId):
        parentArea = get_by_id(areaId=parentId)
        parentArea.add_child(self.areaId)

        return self

    def add_child(self, childId):
        areaParent = AreaAreaModel(parentAreaId=self.areaId, childAreaId=childId)
        db.session.add(areaParent)
        db.session.commit()

        return self

    def get_associated_areas(self, areaType):
        return get_associated_areas(self, areaType);
    #
    # @hybrid_property
    # def pollingStations(self):
    #     # return []
    #     visitedAreas = []
    #     return get_child_areas(self, AreaTypeEnum.PollingStation, visitedAreas) \
    #            + get_parent_areas(self, AreaTypeEnum.PollingStation, visitedAreas)
    #
    # @hybrid_property
    # def countingCentres(self):
    #     # return []
    #     visitedAreas = []
    #     return get_child_areas(self, AreaTypeEnum.CountingCentre, visitedAreas) \
    #            + get_parent_areas(self, AreaTypeEnum.CountingCentre, visitedAreas)
    #
    # @hybrid_property
    # def districtCentres(self):
    #     # return []
    #     visitedAreas = []
    #     return get_child_areas(self, AreaTypeEnum.DistrictCentre, visitedAreas) \
    #            + get_parent_areas(self, AreaTypeEnum.DistrictCentre, visitedAreas)



    __mapper_args__ = {
        'polymorphic_on': areaType
    }


class AreaAreaModel(db.Model):
    __tablename__ = 'area_area'
    parentAreaId = db.Column(db.Integer, db.ForeignKey("area.areaId"), primary_key=True)
    childAreaId = db.Column(db.Integer, db.ForeignKey("area.areaId"), primary_key=True)


Model = AreaModel


def get_associated_areas(area, areaType):
    visitedAreas = []
    return get_child_areas(area, areaType, visitedAreas) + get_parent_areas(area, areaType, visitedAreas)


def get_child_areas(area, areaType, visitedAreas=[]):
    result = []

    if area.areaId not in visitedAreas:
        if len(visitedAreas) > 0 and area.areaType is areaType:
            # Avoid the source area being the result
            visitedAreas.append(area.areaId)
            result.append(area)
            return result
        elif area.areaType is AreaTypeEnum.PollingStation:
            # Redirecting to parents since polling stations has not children because it
            # an entity between electorates and other offices.
            result = get_parent_areas(area, areaType, visitedAreas)
            return result
        else:
            visitedAreas.append(area.areaId)
            for child in area.children:
                result = result + get_child_areas(child, areaType, visitedAreas=visitedAreas)

    return result


def get_parent_areas(area, areaType, visitedAreas=[]):
    result = []

    if area.areaId not in visitedAreas:
        if len(visitedAreas) > 0 and area.areaType is areaType:
            # Avoid the source area being the result
            visitedAreas.append(area.areaId)
            result.append(area)
            return result
        else:
            visitedAreas.append(area.areaId)
            for parent in area.parents:
                result = result + get_parent_areas(parent, areaType, visitedAreas=visitedAreas)

    return result


def create(areaName, areaType, electionId):
    area = Model(
        areaName=areaName,
        areaType=areaType,
        electionId=electionId
    )

    return area


def get_all():
    query = Model.query
    result = query.all()

    return result


def get_by_id(areaId):
    result = Model.query.filter(
        Model.areaId == areaId
    ).one_or_none()

    return result