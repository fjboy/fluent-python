

from concurrent import futures


def run_concurrent(fn, maps=None, nums=None, max_workers=None):

    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        if maps:
            tasks = executor.map(fn, maps)
        elif nums:
            tasks = [executor.submit(fn) for i in range(maps)]
        for task in tasks:
            task.done()
            yield
