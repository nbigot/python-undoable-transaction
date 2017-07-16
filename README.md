# undoable_transaction

[![Build Status](https://travis-ci.org/nbigot/python-undoable-transaction.svg?branch=master)](https://travis-ci.org/nbigot/python-undoable-transaction)

Python package for undoable transaction


## Installation

Supported in python version 3.x and 2.7

```
pip install undoable_transaction
```

## Get it from pypi

https://pypi.python.org/pypi/undoable_transaction


## Simple example

```python
from undoable_transaction.transaction import Transaction


def run():
    def commit_step1(c):
        c['logger'].info("commit_step1")

    def rollback_step1(c):
        c['logger'].info("rollback_step1")

    def panic_step1(c):
        c['logger'].info("panic_step1")

    def rollback_step2(c):
        c['logger'].info("rollback_step2")

    def raise_fake_error(c, e):
        if c['context']['simulate_error'] == 1:
            raise ValueError(e)
        return True

    # define all transaction steps here (each tuple is a step)
    trans_desc_scenario = [
        ('step #0 : create user',
         lambda c: Transaction.log_fn(c, 'info', 'my commit step 0: create user'),
         lambda c: Transaction.log_fn(c, 'warning', 'my rollback step 0: delete created user'),
         lambda c: Transaction.log_fn(c, 'error', 'my panic step 0: clean not deleted user')),
        ('label step #1', commit_step1, rollback_step1, panic_step1),
        ('label step #2', lambda c: True, rollback_step2, None),
        (None, None, None, None),
        {'commit': lambda c: raise_fake_error(c, 'fake error')}
    ]

    trans_context = {
        # put all you need in there
        'commits': [],
        'rollbacks': [],
        'history': [],
        'common': {},
        'simulate_error': simulate_error
    }

    trans = Transaction(logger=logging, transaction_description=trans_desc_scenario)
    result = trans.run(context=trans_context)



def init_log():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


init_log()
run()
print("end.")
```


## Summary list of directories to look at:

| **What**          | **Directory**                        |
|-------------------|--------------------------------------|
|source code        |_undoable_transaction/_               |
|tests              |_test/_                               |


## License

MIT

