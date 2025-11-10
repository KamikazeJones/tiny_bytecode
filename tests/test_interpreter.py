import unittest
from interpreter import TinyBytecodeVM


def run_text(text: str) -> TinyBytecodeVM:
    vm = TinyBytecodeVM()
    vm.run_text(text)
    return vm


class TestTinyBytecode(unittest.TestCase):
    def test_double(self):
        vm = run_text("4 *")
        self.assertEqual(vm.data_stack, [8])

    def test_call_and_return(self):
        prog = "$sub & :sub 2 3 + ;"
        vm = run_text(prog)
        self.assertEqual(vm.data_stack, [5])

    def test_memory_access(self):
        vm = run_text("0 10 ! 0 @")
        self.assertEqual(vm.data_stack, [10])


if __name__ == '__main__':
    unittest.main()
