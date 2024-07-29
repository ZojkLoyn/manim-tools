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

    @classmethod
    def from_function(cls, stated_keys: list[str], func: FunctionType,
                      mobject: Mobject, *args, **kwargs):
        mobject.generate_target()
        target = mobject.target
        func(target, *args, **kwargs)
        stated_kwargs = __subdict(target, stated_keys)
        return cls(stated_kwargs, MoveToTarget, mobject)

    @classmethod
    def from_method(cls, stated_keys: list[str], method: MethodType, *args,
                    **kwargs):
        return cls.from_function(stated_keys, method.__func__, method.__self__,
                                 *args, **kwargs)

    def begin(self):
        self.animation.begin()

    def update_mobjects(self, dt):
        self.animation.update_mobjects(dt)

    def interpolate(self, alpha):
        self.animation.interpolate(alpha)

    def finish(self):
        self.animation.finish()
        self.mobject.__dict__.update(self.stated_kwargs)


def StatedFunction(*stated_keys):

    def decorator(func: FunctionType):

        def wrapper(mobject: Mobject,
                    *args,
                    return_animation: bool = False,
                    **kwargs):
            if return_animation:
                return StatedAnimation.from_function(stated_keys, func,
                                                     mobject, *args, **kwargs)
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




### test ###


from manim_tools_pseudocode import *
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
        logger = self._show(mobj,TestScene.unstated_code)

        stated_mobj = TestScene.StatedInt().shift(RIGHT * 2)
        stated_logger = self._show(stated_mobj,TestScene.unstated_code)

    @pseudocode(
        "789c8b8e562a2e492c2a3154d28956cacd4fcad22b4e2d892f4bcc294dd530d454d2512a4ecd49d32bc849acd408cec82f772e4a4d2cc9cccfd30029d5d4548a8d056a33c2a2d70855af675e4a667262492a8a3e6390be90d4e292e0e4d4bc5484e6f8b4d2bc64b04a1d056322cc310199835083ea121d0513a83253fcca4ca1cab20bd01462b5d31c8b9fcd09b935160071d577ec"
    )
    def unstated_code(s1):
        mobj.set_value(1)
        self.play(ShowCreation(mobj))
        ### 2
        mobj.set_value(2)
        self.play(Indicate(mobj))
        ### 3
        TestScene.set_value_func(mobj, 3)
        self.play(Indicate(mobj))
        ### 4
        self.play(mobj.set_value, 4)
        ### 5
        self.play(mobj.set_value, 5)
        ### kp5
        self.play(Indicate(mobj))
        ### 7
        mobj.set_value(7)
        self.play(Indicate(mobj))

    def _show(self, mobj: Integer, code) -> Integer:
        logger = Integer().next_to(mobj, DOWN)
        logger.add_updater(lambda self: self.set_value(mobj.get_value()))
        scene_title = Text("Scene:").next_to(mobj, LEFT)
        logger_title = Text("Real :").next_to(logger, LEFT)
        self.add(logger, scene_title, logger_title)

        for _, lines in code():
            exec("\n".join(lines),globals(),locals())
        
        return logger
