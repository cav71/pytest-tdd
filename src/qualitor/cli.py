import argparse


class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = MyFormatter
        if "doc" in kwargs:
            description, _, epilog = (kwargs.pop("doc") or "").partition("\n")
            kwargs["description"] = kwargs.get("description", description)
            kwargs["epilog"] = kwargs.get("epilog", epilog)
        super().__init__(**kwargs)

