"""Registry of every pipeline stage, in run order.

Numbering has a gap (03 -> 13): stages 04-12 were an earlier
single-neighborhood draft, superseded and removed rather than left to
confuse a rerun (see README). Stage 30 was originally a static citywide FEMA
flood-polygon fetch, superseded by the live in-map FEMA fetch in stage 23 and
removed -- the number was later reused for the real HPD crime-risk stage
below rather than left permanently retired.

Note ALL_STAGES is NOT in numeric id order: stage 30 (crime risk) must run
before stage 20 (scoring) despite its higher number, since scoring consumes
its output; stage 23 (map generation) reads the outputs of stages 24-29, so
it must run after them despite its lower number. Both are slotted into
ALL_STAGES at the point they actually need to run, matching the pipeline's
real dependency order rather than numeric id order.
"""
from __future__ import annotations

from .s01_fetch_tracts import FetchTractsStage
from .s02_fetch_competitors import FetchCompetitorsStage
from .s03_gap_analysis import GapAnalysisStage
from .s13_houston_scope_clusters import HoustonScopeClustersStage
from .s14_find_intersections_citywide import FindIntersectionsCitywideStage
from .s15_fetch_parcels_citywide import FetchParcelsCitywideStage
from .s16_fetch_citywide_aadt import FetchCitywideAadtStage
from .s17_fetch_citywide_blockgroups import FetchCitywideBlockgroupsStage
from .s18_enrich_sites_citywide import EnrichSitesCitywideStage
from .s19_drive_times_and_huff import DriveTimesAndHuffStage
from .s20_score_sites_citywide import ScoreSitesCitywideStage
from .s21_fetch_houston_tract_geometry import FetchHoustonTractGeometryStage
from .s22_isochrone_winner import IsochroneWinnerStage
from .s23_generate_map_citywide import GenerateMapStage
from .s24_cannibalization_analysis import CannibalizationAnalysisStage
from .s25_extended_demographics_and_ci import ExtendedDemographicsAndCiStage
from .s26_microsite_details import MicrositeDetailsStage
from .s27_vehicle_tenure_demographics import VehicleTenureDemographicsStage
from .s28_sensitivity_analysis import SensitivityAnalysisStage
from .s29_statistical_rigor import StatisticalRigorStage
from .s30_crime_risk import CrimeRiskStage
from .s31_generate_slide_assets import GenerateSlideAssetsStage

ALL_STAGES = [
    FetchTractsStage(),
    FetchCompetitorsStage(),
    GapAnalysisStage(),
    HoustonScopeClustersStage(),
    FindIntersectionsCitywideStage(),
    FetchParcelsCitywideStage(),
    FetchCitywideAadtStage(),
    FetchCitywideBlockgroupsStage(),
    EnrichSitesCitywideStage(),
    DriveTimesAndHuffStage(),
    CrimeRiskStage(),
    ScoreSitesCitywideStage(),
    FetchHoustonTractGeometryStage(),
    IsochroneWinnerStage(),
    CannibalizationAnalysisStage(),
    ExtendedDemographicsAndCiStage(),
    MicrositeDetailsStage(),
    VehicleTenureDemographicsStage(),
    SensitivityAnalysisStage(),
    StatisticalRigorStage(),
    GenerateMapStage(),
    GenerateSlideAssetsStage(),
]

__all__ = ["ALL_STAGES"]
