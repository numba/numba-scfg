from byteflow2 import ByteFlow, ByteFlowRenderer
from simulator import Simulator
from pprint import pprint
from dis import dis
import unittest

#    flow = ByteFlow.from_bytecode(foo)
#    #pprint(flow.bbmap)
#    flow = flow.restructure()
#    #pprint(flow.bbmap)
#    # pprint(rtsflow.bbmap)
#    ByteFlowRenderer().render_byteflow(flow).view()
#    print(dis(foo))
#
#    sim = Simulator(flow, foo.__globals__)
#    ret = sim.run(dict(x=1))
#    assert ret == foo(x=1)
#
#    #sim = Simulator(flow, foo.__globals__)
#    #ret = sim.run(dict(x=100))
#    #assert ret == foo(x=100)

# You can use the following snipppet to visually debug the restructured
# byteflow:
#
#    ByteFlowRenderer().render_byteflow(flow).view()
#
#

class SimulatorTest(unittest.TestCase):

    def _run(self, func, flow, kwargs):
        with self.subTest():
            sim = Simulator(flow, func.__globals__)
            self.assertEqual(sim.run(kwargs), func(**kwargs))

    def test_simple_branch(self):

        def foo(x):
            c = 0
            if x:
                c += 100
            else:
                c += 1000
            return c

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        # if case
        self._run(foo, flow, {'x': 1})
        # else case
        self._run(foo, flow, {'x': 0})

    def test_andor(self):

        def foo(x, y):
            return (x > 0 and x < 10) or (y > 0 and y < 10)

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        self._run(foo, flow, {'x': 5, 'y': 5})

    def test_while_count(self):

        def foo(s, e):
            i = s
            c = 0
            while i < e:
                c += i
                i += 1
            return c

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        ByteFlowRenderer().render_byteflow(flow).view()

        self._run(foo, flow, {'s': 0, 'e': 0})
        self._run(foo, flow, {'s': 0, 'e': 1})


    def test_simple_for_loop(self):


        def foo(x):
            c = 0
            for i in range(x):
                c += i
            return c

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        # loop bypass case
        self._run(foo, flow, {'x': 0})
        # loop case
        self._run(foo, flow, {'x': 2})
        # extended loop case
        self._run(foo, flow, {'x': 100})

    def test_for_loop_with_exit(self):

        def foo(x):
            c = 0
            for i in range(x):
                c += i
                if i == 100:
                    break
            return c

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        # loop bypass case
        self._run(foo, flow, {'x': 0})
        # loop case
        self._run(foo, flow, {'x': 2})
        # break case
        self._run(foo, flow, {'x': 15})

    def test_nested_for_loop_with_break_and_continue(self):

        def foo(x):
            c = 0
            for i in range(x):
                c += i
                if c <= 0:
                    continue
                else:
                    for j in range(c):
                        c += j
                        if c > 100:
                            break
            return c

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        self._run(foo, flow, {'x': 0})
        self._run(foo, flow, {'x': 5})

    def test_for_loop_with_multiple_backedges(self):

        def foo(x):
            c = 0
            for i in range(x):
                if i == 3:
                    c += 100
                elif i == 5:
                    c += 1000
                else:
                    c += 1
            return c

        flow = ByteFlow.from_bytecode(foo)
        flow = flow.restructure()

        # loop bypass
        self._run(foo, flow, {'x': 0})
        # default on every iteration
        self._run(foo, flow, {'x': 2})
        # adding 100, via the if clause
        self._run(foo, flow, {'x': 4})
        # adding 1000, via the elif clause
        self._run(foo, flow, {'x': 7})

if __name__ == "__main__":
    #test_simple_for_loop()
    #test_for_loop_with_exit()
    #test_bar()
    #test_for_loop_with_multiple_backedges()
    unittest.main()
