import os, time, random, string, numpy

def fuzzer_test(fuzzer_path, num_iterations, seed_inputs):
    try:
        i = 0
        seconds = [-1 for x in range(num_iterations)]
        while i < num_iterations:
            input_i = seed_inputs[i]
            start = time.time()
            wait_status = os.system(f'python3 {fuzzer_path} {input_i}')
            end = time.time()
            exit_code = os.waitstatus_to_exitcode(wait_status)
            if exit_code == 219:
                total_time = end - start
                seconds[i] = total_time
            i += 1
        print(seconds)
        secs = [s for s in seconds if s != -1]
        file_name = fuzzer_path[:-3] + ".csv"
        print(file_name + ": ")
        print(str(len(secs)) + " bugs found")
        if len(secs) > 0:
            mean = sum(secs) / len(secs) 
            variance = sum((i - mean) ** 2 for i in secs) / len(secs)
            print("Mean: " + str(mean))
            print("Variance: " + str(variance))
            secs.append(mean)
            secs.append(variance)
        np_seconds = numpy.array(secs)
        numpy.savetxt(file_name, np_seconds, delimiter=",")
    except:
        # print(e)
        print(f'Path invalid')

if __name__ == "__main__":
    num_iterations = 100
    random.seed(10)
    seed_inputs = []
    for i in range(num_iterations):
        input_i = ''.join(random.choices(string.ascii_lowercase, k=20))
        seed_inputs.append(input_i)
    fuzzer_test('baseline_fuzzer_test.py', num_iterations, seed_inputs)
    fuzzer_test('student_fuzzer_test.py', num_iterations, seed_inputs)
