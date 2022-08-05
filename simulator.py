
from collections import defaultdict, ChainMap
from dis import Instruction
from byteflow2 import ByteFlow, BlockMap, BCLabel, BasicBlock
import builtins

class Simulator:
    """BlockMap simulator"""
    def __init__(self, flow: ByteFlow, globals: dict):
        self.flow = flow
        self.bcmap = {inst.offset: inst for inst in flow.bc}
        self.varmap = dict()
        self.globals = ChainMap(globals, builtins.__dict__)
        self.stack = []
        self.branch = None
        self.return_value = None

    def run(self, args):
        self.varmap.update(args)
        target = BCLabel(0)
        while True:
            bb = self.flow.bbmap.graph[target]
            action = self.run_bb(bb)
            if "return" in action:
                return action["return"]
            target = action["jumpto"]

    def run_bb(self, bb: BasicBlock):
        assert isinstance(bb, BasicBlock)
        pc = bb.begin.offset
        while pc < bb.end.offset:
            inst = self.bcmap[pc]
            self.run_inst(inst)
            pc += 2
        if bb.fallthrough or  len(bb.jump_targets) == 1:
            [target] = bb.jump_targets
            return {"jumpto": target}
        elif bb.jump_targets:
            [br_false, br_true] = bb.jump_targets
            return {"jumpto": br_true if self.branch else br_false}
        else:
            return {"return": self.return_value}

    def run_inst(self, inst: Instruction):
        print('----', inst)
        print(self.varmap)
        print(self.stack)
        handler = getattr(self, f"op_{inst.opname}")
        handler(inst)

    def op_LOAD_CONST(self, inst):
        self.stack.append(inst.argval)

    def op_LOAD_FAST(self, inst):
        self.stack.append(self.varmap[inst.argval])

    def op_LOAD_GLOBAL(self, inst):
        v = self.globals[inst.argval]
        self.stack.append(v)

    def op_STORE_FAST(self, inst):
        val = self.stack.pop()
        self.varmap[inst.argval] = val

    def op_CALL_FUNCTION(self, inst):
        args = [self.stack.pop() for _ in range(inst.argval)][::-1]
        fn = self.stack.pop()
        res = fn(*args)
        self.stack.append(res)

    def op_GET_ITER(self, inst):
        val = self.stack.pop()
        res = iter(val)
        self.stack.append(res)

    def op_FOR_ITER(self, inst):
        tos = self.stack[-1]
        try:
            ind = next(tos)
        except StopIteration:
            self.branch = False
        else:
            self.branch = True
            self.stack.append(ind)

    def op_INPLACE_ADD(self, inst):
        rhs = self.stack.pop()
        lhs = self.stack.pop()
        lhs += rhs
        self.stack.append(lhs)

    def op_RETURN_VALUE(self, inst):
        v = self.stack.pop()
        self.return_value = v

    def op_JUMP_ABSOLUTE(self, inst):
        return