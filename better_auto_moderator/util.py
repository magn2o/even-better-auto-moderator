from ruamel import yaml

def to_yaml_string(obj):
    safe_yaml=yaml.YAML()
    class DumpStream:
        def __init__(self):
            self.val = ""

        def write(self, s):
            if s == "...\n":
                return
            self.val = self.val + s.decode('utf-8')

    dump = DumpStream()
    safe_yaml.dump(obj, stream=dump)
    return "\n"+dump.val if dump.val[0] == "-" else dump.val
