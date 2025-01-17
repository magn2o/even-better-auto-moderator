from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, ModeratorAuthorChecks, ModeratorActions, ModeratorAuthorActions, comparator
from better_auto_moderator.moderators.post_moderator import PostModeratorChecks, PostModeratorActions
from better_auto_moderator.rule import Rule
from better_auto_moderator.reddit import reddit

def comment_depth(comment):
    if (hasattr(comment, 'depth')):
        return comment.depth

    forest = comment.submission.comments
    forest.replace_more()
    return [curr for curr in forest.list() if curr.id == comment.id][0].depth

class CommentModerator(Moderator):
    @cached_property
    def actions(self):
        return CommentModeratorActions(self)

    @cached_property
    def checks(self):
        return CommentModeratorChecks(self)

class CommentModeratorChecks(ModeratorChecks):
    def author(self, value, rule, options):
        author_checks = CommentModeratorAuthorChecks(self.moderator)
        author_rule = Rule(value)
        return self.moderator.check(author_rule, checks=author_checks)

    def parent_author(self, value, rule, options):
        author_checks = ModeratorAuthorChecks(self.moderator)
        author_checks.item = self.item.submission if self.item.is_root else self.item.parent()
        author_rule = Rule(value)
        return self.moderator.check(author_rule, checks=author_checks)

    def parent_submission(self, value, rule, options):
        post_checks = PostModeratorChecks(self.moderator)
        post_checks.item = self.item.submission
        post_rule = Rule(value)
        return self.moderator.check(post_rule, checks=post_checks)

    def parent_comment(self, value, rule, options):
        if comment_depth(self.item) == 0:
            return None

        comment_checks = CommentModeratorChecks(self.moderator)
        comment_checks.item = self.item.parent()
        comment_rule = Rule(value)
        return self.moderator.check(comment_rule, checks=comment_checks)

    @comparator(default='bool')
    def is_top_level(self, rule, options):
        return comment_depth(self.item) == 0

class CommentModeratorAuthorChecks(ModeratorAuthorChecks):
    @comparator(default='bool')
    def is_submitter(self, rule, options):
        return self.item.author.id == self.item.submission.author.id

class CommentModeratorActions(ModeratorActions):
    def parent_author(self, rule, value):
        author_actions = ModeratorAuthorActions(self.moderator)
        author_actions.item = self.item.submission if self.item.is_root else self.item.parent()
        author_rule = Rule(value)
        return self.moderator.action(author_rule, actions=author_actions)

    def parent_submission(self, rule, value):
        post_actions = PostModeratorActions(self.moderator)
        post_actions.item = self.item.submission
        post_rule = Rule(value)
        return self.moderator.action(post_rule, actions=post_actions)

    def parent_comment(self, rule, value):
        if comment_depth(self.item) == 0:
            return None

        comment_actions = CommentModeratorActions(self.moderator)
        comment_actions.item = self.item.parent()
        comment_rule = Rule(value)
        return self.moderator.action(comment_rule, actions=comment_actions)
