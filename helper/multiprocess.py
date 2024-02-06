import multiprocessing


def run_function_on_process(function, *args) -> multiprocessing.Process:
    """Run the specified function on a new process."""
    new_process = multiprocessing.Process(target=function, args=args)
    new_process.daemon = True
    new_process.start()
    return new_process
