"""
V1.7 Oxidation Factory Complete Financial Assistant

This package integrates:
- V1.6 Practical Enhancement features (storage, import, reports, reconciliation, reminders)
- V1.5 Workflow Optimization features (smart dashboard, workflow engine, one-click operations)
- Oxidation factory industry-specific features (pricing units, outsourced processing, industry classification)

Designed for small oxidation factories with non-technical accountants.
"""

__version__ = "1.7.0"
__author__ = "Financial Assistant Team"

# Core modules from V1.6
from . import models
from . import storage
from . import core
from . import config
from . import import_engine
from . import reports
from . import reconciliation
from . import reminders
from . import ui

# Workflow modules from V1.5
from . import workflow

# Industry-specific modules (new in V1.7)
from . import industry

__all__ = [
    "models",
    "storage",
    "core",
    "config",
    "import_engine",
    "reports",
    "reconciliation",
    "reminders",
    "ui",
    "workflow",
    "industry",
]
