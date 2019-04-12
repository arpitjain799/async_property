import asyncio
from async_property.cached import AsyncCachedPropertyDescriptor

is_coroutine = asyncio.iscoroutinefunction


AWAIT_LOADER_ATTR = '_async_property_loaders'


def get_loaders(instance):
    return getattr(instance, AWAIT_LOADER_ATTR, {})


class AwaitLoaderMeta(type):
    def __new__(mcs, name, bases, attrs) -> type:
        loaders = {}
        for key, value in attrs.items():
            if isinstance(value, AsyncCachedPropertyDescriptor):
                loaders[key] = value.get_loader

        for base in reversed(bases):
            for key, loader in get_loaders(base).items():
                if key not in loaders:
                    loaders[key] = loader

        attrs[AWAIT_LOADER_ATTR] = loaders
        return super().__new__(mcs, name, bases, attrs)


class AwaitLoader(metaclass=AwaitLoaderMeta):
    def __await__(self):
        return self._load().__await__()

    async def _load(self):
        """
        Calls overridable async load method
        and then calls async property loaders
        """
        if hasattr(self, 'load') and is_coroutine(self.load):
            await self.load()
        loaders = get_loaders(self)
        if loaders:
            await asyncio.wait([
                get_loader(self)()
                for get_loader
                in loaders.values()
            ])
        return self
