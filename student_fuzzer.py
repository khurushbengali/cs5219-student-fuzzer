from types import FrameType
from fuzzingbook import GreyboxFuzzer as gbf
from fuzzingbook import Coverage as cv
from fuzzingbook import MutationFuzzer as mf

from typing import Callable, List, Optional, Set, Any, Tuple, Dict, Union

import traceback
import numpy as np
import time
import inspect

from bug import entrypoint
from bug import get_initial_corpus

## You can re-implement the coverage class to change how
## the fuzzer tracks new behavior in the SUT

class MyCoverage(cv.Coverage):
    not_offset = True
    lines = [""] + inspect.getsource(entrypoint).splitlines()
    starting_branch_line = [2]
    for l in range(len(lines)):
        if 'if' in lines[l] or 'elif' in lines[l] or 'else' in lines[l] or 'case' in lines[l]:
            starting_branch_line.append(l+1)

    def __init__(self) -> None:
        """Constructor"""
        self._trace: List[cv.Location] = []
        self.branch_coverage = []
        self.storage_n_gram = []
        self.counter_n_gram = 0
        self.nesting_degree_checker = []
        self.nesting_degree_counter = 0

    def traceit(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        """Tracing function. To be overloaded in subclasses."""        
        if self.original_trace_function is not None:
            self.original_trace_function(frame, event, arg)
        if event == "line":
            f_name = frame.f_code.co_name
            lineno = frame.f_lineno
            if MyCoverage.not_offset and f_name == 'entrypoint':
                MyCoverage.not_offset = False
                offset = lineno - MyCoverage.starting_branch_line[0]
                for i in range(len(MyCoverage.starting_branch_line)):
                    MyCoverage.starting_branch_line[i] += offset
            if f_name != '__exit__':  # avoid tracing ourselves:
                self.nesting_degree_checker.append(lineno)
                self.nesting_degree_counter += 1
                if self.nesting_degree_counter == 5:
                    self.nesting_degree_counter = 0
                    self.nesting_degree_checker = []

                if lineno in MyCoverage.starting_branch_line:
                    self.storage_n_gram.append(lineno)
                    self.counter_n_gram += 1
                    if self.counter_n_gram == 5:
                        self.counter_n_gram = 0
                        self.branch_coverage.append(tuple(self.storage_n_gram))
                        self.storage_n_gram = []
        return self.traceit

    def coverage(self):
        """The set of executed lines, as (f_name, line_number) pairs"""
        if self.counter_n_gram > 0:
            while self.counter_n_gram < 5:
                self.counter_n_gram += 1
                self.storage_n_gram.append(0)
            self.branch_coverage.append(tuple(self.storage_n_gram))
            self.counter_n_gram = 0
            self.storage_n_gram = []
        nested_tuple = tuple((self.nesting_degree_checker))
        return self.branch_coverage + [nested_tuple]

## You can re-implement the runner class to change how
## the fuzzer tracks new behavior in the SUT

class MyFunctionCoverageRunner(mf.FunctionRunner):
    def run_function(self, inp: str) -> Any:
        with MyCoverage() as cov:
            try:
                result = super().run_function(inp)
            except Exception as exc:
                self._coverage = cov.coverage()
                raise exc
        self._coverage = cov.coverage()
        return result
    def coverage(self):
        return self._coverage


# class MyRunner(mf.FunctionRunner):
#
#     def run_function(self, inp):
#           <your implementation here>
#
#     def coverage(self):
#           <your implementation here>
#
#     etc...


## You can re-implement the fuzzer class to change your
## fuzzer's overall structure

# class MyFuzzer(gbf.GreyboxFuzzer):
#
#     def reset(self):
#           <your implementation here>
#
#     def run(self, runner: gbf.FunctionCoverageRunner):
#           <your implementation here>
#   etc...

## The Mutator and Schedule classes can also be extended or
## replaced by you to create your own fuzzer!


    
# When executed, this program should run your fuzzer for a very 
# large number of iterations. The benchmarking framework will cut 
# off the run after a maximum amount of time
#
# The `get_initial_corpus` and `entrypoint` functions will be provided
# by the benchmarking framework in a file called `bug.py` for each 
# benchmarking run. The framework will track whether or not the bug was
# found by your fuzzer -- no need to keep track of crashing inputs
if __name__ == "__main__":
    seed_inputs = get_initial_corpus()
    fast_schedule = gbf.AFLFastSchedule(5)
    line_runner = MyFunctionCoverageRunner(entrypoint)

    fast_fuzzer = gbf.CountingGreyboxFuzzer(seed_inputs, gbf.Mutator(), fast_schedule)
    fast_fuzzer.runs(line_runner, trials=9999999999)