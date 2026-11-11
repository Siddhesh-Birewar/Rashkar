"""Re-exports CropNet Extra Income catalog and engines under `app.rashkar.engines`."""

try:
    from cropnet.services.api.app.services.income.catalog import (
        EXTENDED_OPPORTUNITY_CATALOG,
        get_opportunity_by_id,
    )
    from cropnet.services.api.app.services.income.engine import IncomeEngine
    from cropnet.services.api.app.services.income.feasibility import (
        OpportunityFeasibilityEngine,
    )
    from cropnet.services.api.app.services.income.financial import (
        IncomeFinancialService,
    )
except ImportError:
    from app.services.income.catalog import (
        EXTENDED_OPPORTUNITY_CATALOG,
        get_opportunity_by_id,
    )
    from app.services.income.engine import IncomeEngine
    from app.services.income.feasibility import OpportunityFeasibilityEngine
    from app.services.income.financial import IncomeFinancialService

__all__ = [
    "EXTENDED_OPPORTUNITY_CATALOG",
    "get_opportunity_by_id",
    "IncomeEngine",
    "OpportunityFeasibilityEngine",
    "IncomeFinancialService",
]
