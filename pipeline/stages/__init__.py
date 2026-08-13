"""Registry of every pipeline stage, in run order.

Numbering has gaps (03 -> 13, 29 -> 31): stages 04-12 were an earlier
single-neighborhood draft and stage 30 fetched a static citywide FEMA
flood-polygon file -- both superseded and removed rather than left to
confuse a rerun (see README).

Note ALL_STAGES is NOT in numeric id order: stage 23 (map generation)
reads the outputs of stages 24-29, so it must run after them despite its
lower number -- it's slotted in near the end, matching the pipeline's
actual documented run order.
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
