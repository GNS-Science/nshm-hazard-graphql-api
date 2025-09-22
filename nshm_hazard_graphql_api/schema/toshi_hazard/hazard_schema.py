"""Schema objects for hazard."""

import graphene


class HazardCodedLocation(graphene.ObjectType):
    lat = graphene.Float()
    lon = graphene.Float()
    code = graphene.String()
    name = graphene.String(required=False)
    key = graphene.String(required=False)


class GriddedLocation(HazardCodedLocation):
    resolution = graphene.Float()


class ToshiHazardCurve(graphene.ObjectType):
    """Represents one set of level and values for a hazard curve."""

    levels = graphene.List(graphene.Float, description="IMT levels.")
    values = graphene.List(graphene.Float, description="Hazard values.")


class ToshiHazardResult(graphene.ObjectType):
    """All the info about a given curve."""

    hazard_model = graphene.String()
    loc = graphene.String()
    imt = graphene.String()
    agg = graphene.String()
    vs30 = graphene.Float()
    curve = graphene.Field(ToshiHazardCurve)


class ToshiHazardCurveResult(graphene.ObjectType):
    ok = graphene.Boolean()
    locations = graphene.List(GriddedLocation, required=False)
    curves = graphene.List(ToshiHazardResult)


class GriddedLocationResult(graphene.ObjectType):
    location = graphene.Field(GriddedLocation)
    ok = graphene.Boolean()


class DisaggregationReport(graphene.ObjectType):
    """All the info about a given disagg report."""

    hazard_model = graphene.String()
    location = graphene.Field(HazardCodedLocation)
    imt = graphene.String()
    poe = graphene.Float()
    vs30 = graphene.Int()
    inv_time = graphene.Int()
    report_url = graphene.String()


class DisaggregationReportResult(graphene.ObjectType):
    ok = graphene.Boolean()
    reports = graphene.List(DisaggregationReport, required=False)
