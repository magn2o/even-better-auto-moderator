from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, comparator

class ReportModerator(Moderator):
    @cached_property
    def checks(self):
        return ReportModeratorChecks(self)

class ReportModeratorChecks(ModeratorChecks):
    @comparator(default='numeric')
    def rule_number(self, rule, value):
        for count, item in enumerate(self.item.subreddit.rules, start=1):
            if item.violation_reason == [report[0] for report in self.item.mod_reports][0]:
                return count

        return 0

    # @comparator(default='bool')
    # def mod_reports(self, rule, options):
    #     if self.item.mod_reports:
    #         return True
    #     else:
    #         return False

    # @comparator(default='contains')
    # def report_reasons(self, rule, options):
    #     if self.moderator.mod_reports(rule):
    #         reports = self.item.mod_reports
    #     else:
    #         reports = self.item.user_reports
    #         if not self.moderator.are_moderators_exempt(rule):
    #             reports = reports + self.item.mod_reports

    #     return [report[0] for report in reports]