"""Rule Engine Orchestrator"""

from typing import Dict, List, Optional, Type

from app.models.rule import Rule, RuleType
from app.models.team import FantasyTeam
from app.models.validation import RuleViolation, TeamValidationResult, ValidationStatus
from app.services.rules.abstract_rule import AbstractRule
from app.services.rules.budget_cap_rule import BudgetCapRule
from app.services.rules.driver_eligibility_rule import DriverEligibilityRule
from app.services.rules.drs_boost_rule import DRSBoostRule
from app.services.rules.max_teams_rule import MaxTeamsRule
from app.services.rules.roster_size_rule import RosterSizeRule
from app.services.rules.transfer_limit_rule import TransferLimitRule


class RuleEngine:
    """
    Orchestrator for loading and executing validation rules.

    The RuleEngine:
    1. Loads active rules from database
    2. Instantiates appropriate validator classes
    3. Executes all rules against a team
    4. Aggregates violations into a validation result
    """

    # Map rule types to their validator classes
    RULE_VALIDATORS: Dict[RuleType, Type[AbstractRule]] = {
        RuleType.BUDGET_CAP: BudgetCapRule,
        RuleType.ROSTER_SIZE: RosterSizeRule,
        RuleType.DRS_BOOST_REQUIRED: DRSBoostRule,
        RuleType.MAX_TEAMS_PER_USER: MaxTeamsRule,
        RuleType.TRANSFER_LIMIT: TransferLimitRule,
        RuleType.DRIVER_ELIGIBILITY: DriverEligibilityRule,
    }

    def __init__(self):
        """Initialize rule engine"""
        self.rules: List[AbstractRule] = []

    async def load_rules(self, rule_type: Optional[RuleType] = None) -> None:
        """
        Load active rules from database.

        Args:
            rule_type: Optional filter to load only specific rule type
        """
        query = {"is_active": True}

        if rule_type:
            query["rule_type"] = rule_type

        # Load rules from database
        db_rules = await Rule.find(query).to_list()

        # Instantiate validator classes
        self.rules = []
        for db_rule in db_rules:
            validator_class = self.RULE_VALIDATORS.get(db_rule.rule_type)

            if validator_class:
                validator = validator_class(db_rule)
                self.rules.append(validator)
            else:
                print(f"Warning: No validator found for rule type {db_rule.rule_type}")

    async def validate_team(
        self,
        team: FantasyTeam,
        user_team_count: Optional[int] = None,
    ) -> TeamValidationResult:
        """
        Run all loaded rules against a team.

        Args:
            team: Fantasy team to validate
            user_team_count: Optional pre-computed user team count

        Returns:
            TeamValidationResult with all violations
        """
        violations: List[RuleViolation] = []
        warnings: List[RuleViolation] = []
        info: List[RuleViolation] = []

        # Execute each rule
        for rule in self.rules:
            # Handle MaxTeamsRule specially (needs extra context)
            if isinstance(rule, MaxTeamsRule):
                violation = await rule.runRule(team, user_team_count=user_team_count)
            else:
                violation = await rule.runRule(team)

            # Categorize violation by severity
            if violation:
                if violation.severity == "error":
                    violations.append(violation)
                elif violation.severity == "warning":
                    warnings.append(violation)
                elif violation.severity == "info":
                    info.append(violation)

        # Determine overall validation status
        is_valid = len(violations) == 0
        status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID

        # If no errors but has warnings, set status to WARNING
        if is_valid and len(warnings) > 0:
            status = ValidationStatus.WARNING

        # Build summary
        summary = {
            "total_rules_checked": len(self.rules),
            "error_count": len(violations),
            "warning_count": len(warnings),
            "info_count": len(info),
        }

        return TeamValidationResult(
            team_id=team.team_id,
            status=status,
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            info=info,
            summary=summary,
        )

    async def validate_team_quick(self, team: FantasyTeam) -> bool:
        """
        Quick validation that returns only True/False.

        Args:
            team: Fantasy team to validate

        Returns:
            True if valid, False otherwise
        """
        result = await self.validate_team(team)
        return result.is_valid

    def get_loaded_rules(self) -> List[Dict]:
        """
        Get information about currently loaded rules.

        Returns:
            List of rule information dictionaries
        """
        return [
            {
                "rule_id": rule.rule_id,
                "rule_type": rule.rule_type.value,
                "name": rule.name,
                "severity": rule.severity.value,
                "is_active": rule.is_active,
            }
            for rule in self.rules
        ]
