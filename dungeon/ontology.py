import asyncio

END_OF_WORLD = False

class Entity:
    ENTITIES = {}

    def __init__(self, x=0, y=0, name="", description="", owner=None):
        self._position = (x, y)
        self._label = name
        self._description = description
        self._owner = owner
    
    @property
    def position(self):
        return self._position

    @property
    def x(self):
        x, y = self.position
        return x

    @property
    def y(self):
        x, y = self.position
        return y

    @position.setter
    def position(self, new_pos):
        if self._owner is not None:
            self._owner.allow_move(self, new_pos)
        self._position = new_pos

    @property
    def label(self):
        return self._label

    @property
    def description(self):
        return self._description

    @property
    def kind(self):
        return self.__class__.__name__.lower()
    
    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, new_owner):
        if self._owner is not None:
            self._owner.leave(self)
        if new_owner is not None:
            try:
                new_owner.enter(self)
            except:
                if self._owner is not None:
                    self._owner.enter(self)
                raise
        self._owner = new_owner

    @classmethod
    def register(self):
        Entity.ENTITIES[self.__name__] = self

    @classmethod
    def fromxml(self, node):
        cls = Entity.ENTITIES[node.tag]
        newobj = cls(**node.attrib)
        for child in node:
            subobj = self.fromxml(child)
            subobj.owner = newobj
        return newobj

    def runnable(self):
        return ()

class Container:
    def __init__(self, members=()):
        self._members = set(members)

    def enter(self, new_member):
        if new_member is self:
            raise ValueError('an object cannot be put to itself')
        self._members.add(new_member)

    def leave(self, member):
        self._members.discard(member)

    @property
    def members(self):
        return self._members

class Scene(Container, Entity):
    
    def __init__(self, *args, **kwargs):
        super().__init__(())
        super(Container, self).__init__(*args, **kwargs)

    def runnable(self):
        children = []
        for c in self.members:
            children += c.runnable()
        return children

class Room(Scene):

    @property
    def description(self):
        descr = super().description
        descr += "\nThe room contains:"
        for c in self.members:
            descr += f"\na {c.kind}"
        return descr

Room.register()
    
class World(Scene):
    pass

World.register()

class PhysicalEntity(Entity):
    pass

class Box(Container, PhysicalEntity):

    def __init__(self, *args, **kwargs):
        super().__init__()
        super(Container, self).__init__(*args, **kwargs)
        self.is_open = False

    @property
    def description(self):
        descr = super().description
        if self.is_open:
            descr += "\nThe box contains:"
            for c in self.members:
                descr += f"\na {c.kind}"
        return descr

    def open(self):
        self.is_open = True

    def close(self):
        self.is_close = True
    
Box.register()
        
class Scroll(PhysicalEntity):
    pass

Scroll.register()

class ActiveEntity(PhysicalEntity):

    def runnable(self):
        return (self.behaviour(),)

    async def behaviour(self):
        pass

class NPC(ActiveEntity):
    pass

class Troll(NPC):

    async def behaviour(self):
        while not END_OF_WORLD:
            print('Rrrr! Rrrr! Rrrrr!')
            await asyncio.sleep(5)

Troll.register()
