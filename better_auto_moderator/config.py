import tempfile
import os
import re
from ruamel import yaml
from better_auto_moderator.rule import Rule
from better_auto_moderator.reddit import config_subreddit, config_wiki_name, update_automod_config
from better_auto_moderator.util import to_yaml_string

config_last_update_at = 0
rules_last_update_at = 0

def get_configs():
    yaml_rules, yaml_config = get_config_from_wiki()
    if yaml_rules is None:
        return (None, None)

    config = yaml.load(yaml_config.strip(), Loader=yaml.SafeLoader)

    # We are loading variables separately from config, and we need to insert
    # them into the YAML loader context. This special anchored_loader
    # method creates a new yaml.SafeLoader and injects the variables/all_anchors
    # before processing the document. When it's done it, then collects any _new_
    # anchors, and saves those for the next run.
    all_anchors = {}
    def anchored_loader(stream, all_anchors):
        loader = yaml.SafeLoader(stream)
        loader.anchors = all_anchors
        try:
            return loader.get_single_data()
        finally:
            all_anchors = loader.anchors
            loader.dispose()

    if 'variables' in config:
        variables_block = ""
        for d in config['variables']:
            var = list(d)[0]
            # Format values into a value yaml doc
            value = to_yaml_string(d[var])
            variables_block = "%s%s: &%s %s" % (variables_block, var, var, value)

        # Capture variables in all_anchors
        anchored_loader(variables_block, all_anchors)

    raw_rules = [rule.strip() for rule in yaml_rules.split('---')]
    rules = []
    for raw in raw_rules:
        if len(raw) == 0: #Skip empty rules
            continue

        loaded = anchored_loader(raw, all_anchors)
        if loaded is None:
            continue

        rules.append(Rule(loaded, config))
    return (rules, config)

# Read the rules out the subreddit's wiki
def get_config_from_wiki():
    global rules_last_update_at
    global config_last_update_at
    rules = None
    config = None
    for page in config_subreddit.wiki:
        if page.name == config_wiki_name:
            config = page
        if page.name == config_wiki_name + "/rules":
            rules = page

        if rules and config:
            break

    if not rules:
        rules = create_bam_pages(not bool(config))
        config = config_subreddit.wiki[config_wiki_name]

    if rules.revision_date <= rules_last_update_at and config.revision_date <= config_last_update_at:
        return (None, None)
    else:
        rules_last_update_at = rules.revision_date
        config_last_update_at = config.revision_date

    # Strip out the four leading spaces from each line
    rules = '\n'.join([re.sub(r'^    ', '', line) for line in rules.content_md.split('\n')])
    config = '\n'.join([re.sub(r'^    ', '', line) for line in config.content_md.split('\n')])

    return (rules, config)

def create_bam_pages(create_config):
    print('creating bam rules')
    if create_config:
        content = """
    # This is a page created by [BetterAutoModerator](https://github.com/josephwegner/better-auto-moderator)
    # This page contains top-level configurations for BAM - editing this page will modify how BAM behaves
    # If you want to edit a specific rule, check out the %s/rules wiki update_automod_config

    # If set to true, BAM will overwrite /config/automoderator with any rules that can be run by
    # Reddit's AutoModerator. BAM will *not* run those rules, and instead let AutoModerator handle theme entirely
    #
    # NOTE: Backup your automoderator config before turning this on, as it will be lost.
    # It should be saved in revisions, but be safe.
    overwrite_automoderator: false
        """ % config_wiki_name
        page = config_subreddit.wiki.create(config_wiki_name, content, reason="BAM Setup")
        page.mod.update(True, 2) # Lock the page to mods only

    content = """
    # This is a page created by [BetterAutoModerator](https://github.com/josephwegner/better-auto-moderator)
    # This page contains all of the BetterAutoModerator rules. If you need to edit top-level
    # BAM configurations, check out the wiki page above this one.


    # This is an example rule, it doesn't really do anything
    type: modqueue
    report_reason (includes): BAM
    log: "Got a BAM report!"

    ---
    """
    page = config_subreddit.wiki.create(config_wiki_name + "/rules", content, reason="BAM Setup")
    page.mod.update(True, 2) # Lock the page to mods only

    return page

def get_bam_rules(rules):
    bam_rules = []
    for rule in rules:
        if rule.requires_bam:
            bam_rules.append(rule)
    return bam_rules

def get_automod_rules(rules):
    automod_rules = []
    for rule in rules:
        if not rule.requires_bam:
            automod_rules.append(rule)
    return automod_rules

def push_rules(rules):
    rules_for_reddit = []
    for rule in get_automod_rules(rules):
        rules_for_reddit.append(rule.to_reddit())

    # Little bit of formatting here to make it more readable
    full_yaml = "\n---\n\n".join(rules_for_reddit)
    config = """# This subreddit is using BetterAutoModerator, which means that this auto_moderator config has been automatically generated.
# It is NOT a good idea to edit this page directly - it will just get overwritten by BAM later. If you want to add or edit
# existing rules, please go to the %s/rules wiki page and work there. Changes will get moved here automatically.

%s""" % config_wiki_name, full_yaml
    update_automod_config(config)
