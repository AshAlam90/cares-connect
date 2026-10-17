"""CARES Connect calculation engine (pure Python, no UI)."""
from .countries import COUNTRIES, GRID_SCHEMES
from .model import (CostInputs, DesignInputs, FinanceInputs, defaults_for, design_from_dict,
                    design_to_dict, run_design)
from .solar import PVSpec, SiteClimate, fallback_climate, fetch_climate

__all__ = ["COUNTRIES", "GRID_SCHEMES", "CostInputs", "DesignInputs", "FinanceInputs", "PVSpec",
           "SiteClimate", "defaults_for", "design_from_dict", "design_to_dict", "fallback_climate",
           "fetch_climate", "run_design"]
