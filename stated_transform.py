from manimlib import *
from types import *
import inspect


class StatedAnimation(Animation):

    def __init__(self, stated_kwargs: dict[str, object],
                 animation_type: type[Animation], mobject: Mobject, *args,
                 **kwargs):
        self.stated_kwargs = stated_kwargs
        self.animation: Animation = animation_type(mobject, *args, **kwargs)
        super().__init__(mobject)

    def begin(self):
        self.animation.begin()

    def update_mobjects(self, dt):
        self.animation.update_mobjects(dt)

    def interpolate(self, alpha):
        self.animation.interpolate(alpha)

    def finish(self):
        self.animation.finish()
        self.mobject.__dict__.update(self.stated_kwargs)


def StatedFunctionAnimation(stated_keys: list[str], func: FunctionType,
                            mobject: Mobject, *args,
                            **kwargs) -> StatedAnimation:
    mobject.generate_target()
    target = mobject.target
    func(target, *args, **kwargs)
    stated_kwargs = __subdict(target, stated_keys)
    return StatedAnimation(stated_kwargs, MoveToTarget, mobject)


def StatedMethodAnimation(stated_keys: list[str], method: MethodType, *args,
                          **kwargs):
    return StatedFunctionAnimation(stated_keys, method.__func__,
                                   method.__self__, *args, **kwargs)


def StatedFunction(*stated_keys):

    def decorator(func: FunctionType):

        def wrapper(mobject: Mobject,
                    *args,
                    return_animation: bool = False,
                    **kwargs):
            if return_animation:
                return StatedFunctionAnimation(stated_keys, func, mobject,
                                               *args, **kwargs)
            else:
                return func(mobject, *args, **kwargs)

        return wrapper

    return decorator


### tools ###


def __subdict(obj: object, keys: list[str]) -> dict[str, object]:
    return {key: getattr(obj, key) for key in keys if hasattr(obj, key)}


def __kwargs_select(kwargs: dict[str, object],
                    func: FunctionType) -> dict[str, object]:
    para = inspect.signature(func).parameters
    if inspect.Parameter.VAR_KEYWORD in map(lambda x: x.kind, para.values()):
        return kwargs
    else:
        return {
            key: kwargs.get(key)
            for key, value in para.items() if value.kind in {
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY
            } and key in kwargs
        }


class code_pack:

    def __init__(self):
        self.code_pack = []
        self.code_buffer = []

    def buf(self, *code):
        for code_str in code:
            self.code_buffer.append(code_str)
        return self

    def block(self):
        if self.code_buffer:
            self.code_pack.append(self.code_buffer)
            self.code_buffer = []
        return self

    def buf_and_block(self, *code):
        return self.buf(*code).block()

    @property
    def pack(self):
        self.block()
        return self.code_pack

    def exec(self, globals=None, locals=None):
        for block in self.pack:
            for exp in block:
                exec(exp, globals, locals)


### test ###


class TestScene(Scene):

    class StatedInt(Integer):

        @StatedFunction("number")
        def set_value(self, number):
            super().set_value(number)

    @staticmethod
    def set_value_func(mobject: Integer, number):
        mobject.set_value(number)

    def construct(self):
        mobj = Integer().shift(LEFT * 2)
        logger = self._show(mobj)

        stated_mobj = TestScene.StatedInt().shift(RIGHT * 2)
        stated_logger = self._show(stated_mobj)

    unstated_code = code_pack().buf_and_block(
        "mobj.set_value(1)", "self.play(ShowCreation(mobj))").buf_and_block(
            "mobj.set_value(2)", "self.play(Indicate(mobj))").buf_and_block(
                "TestScene.set_value_func(mobj, 3)",
                "self.play(Indicate(mobj))").buf_and_block(
                    "self.play(mobj.set_value, 4)").buf_and_block(
                        "self.play(mobj.set_value, 5)").buf_and_block(
                            "self.play(Indicate(mobj))").buf_and_block(
                                "mobj.set_value(7)",
                                "self.play(Indicate(mobj))")

    def _show(self, mobj: Integer) -> Integer:
        logger = Integer().next_to(mobj, DOWN)
        logger.add_updater(lambda self: self.set_value(mobj.get_value()))
        scene_title = Text("Scene:").next_to(mobj, LEFT)
        logger_title = Text("Real :").next_to(logger, LEFT)
        self.add(logger, scene_title, logger_title)

        TestScene.unstated_code.exec(globals=globals(), locals=locals())

        return logger
