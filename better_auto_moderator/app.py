import praw, prawcore
import better_auto_moderator.config as config
from better_auto_moderator.reddit import subreddit, reddit, config_wiki_name
from better_auto_moderator.reddit import post_edit_stream, comment_edit_stream
from better_auto_moderator.moderators.comment_moderator import CommentModerator
from better_auto_moderator.moderators.modqueue_moderator import ModqueueModerator
from better_auto_moderator.moderators.post_moderator import PostModerator
from better_auto_moderator.moderators.report_moderator import ReportModerator
from better_auto_moderator.rule import Rule
from time import sleep

n = 0
streams = []

print("""

Good day, dear reddit moderator! I hope that your day is filled with ample updoots and gold!
If you're not already aware, the configuration for BetterAutoModerator can be found in your subreddit's wiki,
under the /%s path. Have a good one!

""" % config_wiki_name)

while True:
    # Each iteration we do `n = (n + 1) % 5`... so every 5th iteration we check for new wiki rules
    if n == 0:
        print("Checking for new rules...")
        rules, config_rules = config.get_configs()

        if rules is None or config is None:
            print("Old rules still apply!")
        else:
            print("Applying new rules...")

            if config_rules.get('overwrite_automoderator'):
                config.push_rules(rules)
                rules = config.get_bam_rules(rules)

            streams = []
            # We have to open separate streams for each type of content, so separate them out now
            rules_by_type = {}
            for rule in rules:
                if rule.type not in rules_by_type:
                    rules_by_type[rule.type] = []

                rules_by_type[rule.type].append(rule)

            if "submission" in rules_by_type:
                print("Listening to submission stream...")
                rules = Rule.sort_rules(rules_by_type['submission'])
                streams.append({
                    'stream': subreddit.stream.submissions(pause_after=-1, skip_existing=True),
                    'rules': rules,
                    'moderator': PostModerator
                })
                streams.append({
                    'stream': post_edit_stream(pause_after=-1),
                    'rules': rules,
                    'moderator': PostModerator
                })

            if "comment" in rules_by_type:
                print("Listening to comment stream...")
                rules = Rule.sort_rules(rules_by_type['comment'])
                streams.append({
                    'stream': subreddit.stream.comments(pause_after=-1, skip_existing=True),
                    'rules': rules,
                    'moderator': CommentModerator
                })
                streams.append({
                    'stream': comment_edit_stream(pause_after=-1),
                    'rules': rules,
                    'moderator': CommentModerator
                })


            if "modqueue" in rules_by_type:
                print("Listening to modqueue stream...")
                rules = Rule.sort_rules(rules_by_type['modqueue'])
                streams.append({
                    'stream': subreddit.mod.stream.modqueue(pause_after=-1, skip_existing=True),
                    'rules': rules,
                    'moderator': ModqueueModerator
                })

            if "report" in rules_by_type:
                print("Listening to report stream...")

    # Loop through each of the streams, jumping to the next one when one comes up empty
    for stream in streams:
        try:
            for item in stream['stream']:
                # If we don't get any items from the stream, break and start the next stream
                if item is None:
                    break

                print("Processing %s %s" % (type(item).__name__, item))
                mod = stream['moderator'](item)
                for rule in stream['rules']:
                    ran = mod.moderate(rule)
                    if ran:
                        # If the rule passes, don't apply any additional rules for this item
                        break
	except prawcore.exceptions.BadJSON as e:
		print("PRAW Exception \"{error}\" occurred: ".format(error=e))
	except prawcore.exceptions.ServerError as e:
		print("PRAW Exception \"{error}\" occurred: ".format(error=e))
	except prawcore.exceptions.RequestException as e:
		print("PRAW Exception \"{error}\" occurred: ".format(error=e))
	except praw.exceptions.PRAWException as e:
		print("PRAW Exception \"{error}\" occurred: ".format(error=e))	
	except praw.exceptions.APIException as e:
		print("PRAW Exception \"{error}\" occurred: ".format(error=e))
            
    # Loop through reports looking specifically for mod_reports
    if "report" in rules_by_type:
        rules = Rule.sort_rules(rules_by_type['report'])
        for item in subreddit.mod.reports():
            if item.mod_reports and not item.approved and not item.removed: 
                print("Processing Report on %s %s" % (type(item).__name__, item))
                mod = ReportModerator(item)
                for rule in rules:
                    ran = mod.moderate(rule)
                    if ran:
                        # If the rule passes, don't apply any additional rules for this item
                        break

    n = (n + 1) % 5
    sleep(0.5) # Sleep just a bit each time, to avoid hitting our rate limit
