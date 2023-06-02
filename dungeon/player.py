import ontology
import cmd
import shlex
import itertools
import asyncio
import sys

class Player(ontology.Container, cmd.Cmd, ontology.ActiveEntity):

    __STOPWORDS = ("a", "an", "the", "to", "from", "with", "by", "in", "of")

    def __init__(self, *args, **kwargs):
        super().__init__()
        super(ontology.Container, self).__init__()
        super(cmd.Cmd, self).__init__(*args, **kwargs)
        self.latest_object = None
        self.latest_objects = {}
    
    def _parse_name(self, args):
        prefix = itertools.takewhile(lambda x: x not in Player.__STOPWORDS, args)
        suffix = itertools.dropwhile(lambda x: x not in Player.__STOPWORDS, args)

        return " ".join(prefix), suffix

    def _find_by_kind(self, name):
        return [ obj for obj in self.members | self.owner.members | {self.owner} if obj.kind == name ]

    def _find_by_label(self, name):
        return [ obj for obj in self.members | self.owner.members | {self.owner} if obj.label == name ]

    def _parse(self, args):
        head, *rest = args
        if head == 'myself':
            return self, rest
        if head == 'it':
            if self.latest_object is None:
                raise ValueError('I don\'t know what are you talking about')
            return self.latest_object, rest
        if head == 'a' or head == 'an':
            name, rest = self._parse_name(rest)
            objects = self._find_by_kind(name)
        elif head == 'the':
            name, rest = self._parse_name(rest)
            if name in self.latest_objects:
                return self.latest_objects[name], rest
            raise ValueError(f'I don\'t know what are you talking about: {name}')
        else:
            name, rest = self._parse_name(args)
            objects = self._find_by_label(name)

        if not objects:
            raise ValueError(f'I don\'t know what are you talking about: {name}')
        if len(objects) > 1:
            raise ValueError(f'Ambigous reference: {name}')

        self.latest_object = objects[0]
        self.latest_objects[objects[0].kind] = objects[0]
        return objects[0], rest
    
    def do_inspect(self, line):
        """Inspect an object"""
        args = shlex.split(line)
        object, rest = self._parse(args)
        print(object.description)

    def do_open(self, line):
        """Open an object"""
        args = shlex.split(line)
        object, rest = self._parse(args)
        if isinstance(object, ontology.Box):
            object.open()
        else:
            raise ValueError('I cannot open it')

    def do_open(self, line):
        """Open an object"""
        args = shlex.split(line)
        object, rest = self._parse(args)
        if isinstance(object, ontology.Box):
            object.open()
        else:
            raise ValueError('I cannot open it')

    def do_close(self, line):
        """Close an object"""
        args = shlex.split(line)
        object, rest = self._parse(args)
        if isinstance(object, ontology.Box):
            object.close()
        else:
            raise ValueError('I cannot open it')
        
    def do_bye(self, line):
        """End the game"""
        ontology.END_OF_WORLD = True
        return True

    def do_where(self, line):
        """Where am I?"""
        print(self.owner.description)
        
    def emptyline(self):
        return True
        
    async def behaviour(self):
        while not ontology.END_OF_WORLD:
            try:
                self.cmdloop()
            except Exception as exc:
                print(str(exc), file=sys.stderr)
            except KeyboardInterrupt:
                pass
            await asyncio.sleep(0)

Player.register()
