"""
BSHL Alpha Skill - Replay Package

回放系统，用于历史回测、规则验证和个人进化。
"""

from .case_library import (
    ReplayCase,
    CaseType,
    CaseOutcome,
    ReplayCaseLibrary,
    RuleValidator,
    PerformanceReport,
    replay_case_library,
    rule_validator,
    performance_report,
)
from .replay_engine import (
    ReplayConfig,
    Trade,
    Portfolio,
    ReplayEngine,
    RuleTester,
)
from .personal_evolution import (
    PersonalDecision,
    DecisionType,
    DecisionOutcome,
    PersonalRule,
    PersonalEvolutionEngine,
    get_engine,
)

__all__ = [
    # Case Library
    "ReplayCase",
    "CaseType",
    "CaseOutcome",
    "ReplayCaseLibrary",
    "RuleValidator",
    "PerformanceReport",
    "replay_case_library",
    "rule_validator",
    "performance_report",
    # Replay Engine
    "ReplayConfig",
    "Trade",
    "Portfolio",
    "ReplayEngine",
    "RuleTester",
    # Personal Evolution
    "PersonalDecision",
    "DecisionType",
    "DecisionOutcome",
    "PersonalRule",
    "PersonalEvolutionEngine",
    "get_engine",
]
