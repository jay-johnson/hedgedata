import pandas as pd
from functools import partial
from multiprocessing.pool import ThreadPool
import logging
log = logging.getLogger('')


def chunks(l, n):
    '''MISH'''
    for i in range(0, len(l), n):
        print('yielding', i, i+n)
        yield l[i:i + n]


class Distributer(object):
    def __init__(self, kind, chunkSize=10):
        if kind == 'thread':
            self.pool = ThreadPool(chunkSize)
            self.chunk_size = chunkSize
        else:
            raise NotImplemented

    def distribute(self, function, function_kwargs, iterable, skip_if_error=True, max_attempts=3):
        if isinstance(self.pool, ThreadPool):
            for chunk in chunks(iterable, self.chunk_size):
                attempts = 0
                individually = False

                while attempts < max_attempts:
                    try:
                        if not individually:
                            ret = self.pool.map(partial(function, **function_kwargs), chunk)
                            attempts = max_attempts
                        else:
                            ret = []
                            for item in chunk:
                                try:
                                    val = partial(function, **function_kwargs)(item)
                                    ret.append(val)

                                except Exception as e:
                                    log.critical(e)

                                    attempts += 1
                                    if attempts >= max_attempts:
                                        if skip_if_error:
                                            ret.append(pd.DataFrame())
                                        else:
                                            raise e

                    except Exception as e:
                        log.error(e)
                        attempts += 1
                        if attempts >= max_attempts:
                            individually = True
                            attempts = 0

                for i, item in enumerate(ret):
                    yield (chunk[i], item)

        else:
            raise NotImplemented

    @staticmethod
    def default():
        return Distributer('thread')
