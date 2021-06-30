from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, comparator

class ReportModerator(Moderator):
    @cached_property
    def checks(self):
        return ReportModeratorChecks(self)

class ReportModeratorChecks(ModeratorChecks):
    @comparator(default='numeric')
    def rule_number(self, rule, value):
        report_reason = [report[0] for report in self.item.mod_reports][0];
        for count, item in enumerate(self.item.subreddit.rules, start=1):
            if item.violation_reason == report_reason:
                return count

        return 0