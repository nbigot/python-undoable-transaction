# -*- coding: utf-8 -*-
"""Tests for Transaction"""

import pytest
import logging
import platform
from undoable_transaction.transaction import Transaction


@pytest.fixture()
def init_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if platform.python_version().startswith('2'):
        # python 2
        # log at stdout
        import sys
        ch = logging.StreamHandler(sys.stdout)
    else:
        # python 3
        # log into queue
        import queue
        que = queue.Queue(-1)  # no limit on size
        from logging import handlers
        ch = logging.handlers.QueueHandler(que)

    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    yield ch


@pytest.mark.parametrize("simulate_error,expected", [
    (None, True),
    (1, False),
])
def test_run_scenario_1(init_logger, simulate_error, expected):

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
    assert result is expected
    # (python 3) look at logs: init_logger.queue.queue


@pytest.mark.parametrize("simulate_error,expected", [
    (None, True),
    (0, False),
    (1, False),
    (2, False),
    (3, False),
    (4, False),
])
def test_run_scenario_2(init_logger, simulate_error, expected):

    def scenar2_step0_commit__create_user(context):
        logger = context['logger']
        c = context['context']
        user_name = c['user_name']
        parent_user_id = c['parent_user_id']
        logger.info("want to create user name {} with parent user id {}".format(user_name, parent_user_id))
        # execute sql insert into there ...
        if c['simulate_error'] == 0:
            raise Exception("fake commit error 1")  # simulate error
        user_id = 12345  # fake sql result inserted user_id
        c['created_user_id'] = user_id  # save variable into context
        if c['simulate_error'] in [1, 2, 3, 4]:
            raise Exception("fake commit error 2")  # simulate error
        logger.info("user {} created".format(user_id))

    def scenar2_step0_rollback__create_user(context):
        # delete user only if it has been created
        logger = context['logger']
        c = context['context']
        user_id = c.get('created_user_id')
        if user_id is None:
            # no need to rollback because user has not been created
            return
        else:
            #
            logger.info("delete user {}...".format(user_id))
            # execute sql delete where user_id=%d...
            if c['simulate_error'] == 2:
                raise Exception("fake rollback error")  # simulate error
            logger.info("user {} has been deleted".format(user_id))
            c['deleted_user_id'] = user_id

    def scenar2_step0_panic__create_user(context):
        try:
            logger = context['logger']
            c = context['context']
            user_id = c.get('created_user_id')
            logger.error("rollback failed, cannot delete user {}".format(user_id))
            if c['simulate_error'] == 3:
                raise Exception("fake panic error, no consequence because of try/except")
        except:
            pass
        if context['context']['simulate_error'] == 4:
            raise Exception("fake critical error")  # simulate critical error

    trans_desc_scenario = [
        ('step #0 : create user',
         scenar2_step0_commit__create_user,
         scenar2_step0_rollback__create_user,
         scenar2_step0_panic__create_user)
    ]

    trans_context = {
        'user_name': 'Jean-pierre Madere',
        'parent_user_id': 456789,
        'simulate_error': simulate_error
    }

    trans = Transaction(logger=logging, transaction_description=trans_desc_scenario)
    result = trans.run(context=trans_context)
    assert result is expected
    # (python 3) look at logs: init_logger.queue.queue


@pytest.mark.parametrize("simulate_error,expected", [
    (None, True),
    (0, False),
    (1, False),
    (2, False),
    (3, False),
    (4, False),
])
def test_run_scenario_3(init_logger, simulate_error, expected):

    def commit__create_user(context):
        logger = context['logger']
        c = context['context']
        user_name = c['user_name']
        user_email = c['user_email']
        logger.info("start create user name={} email={}".format(user_name, user_email))
        # execute sql insert into there ...
        if c['simulate_error'] == 0:
            raise Exception("fake commit error 1")  # simulate error
        created_user_id = 12345  # fake sql result inserted user id
        c['created_user_id'] = created_user_id  # save variable into context
        if c['simulate_error'] in [1, 2]:
            raise Exception("fake commit error 2")  # simulate error
        logger.info("user {} created".format(created_user_id))

    def rollback__create_user(context):
        # delete user only if it has been created
        logger = context['logger']
        c = context['context']
        user_id = c.get('created_user_id')
        if user_id is None:
            # no need to rollback because user has not been created
            return
        else:
            logger.info("deleting user {}...".format(user_id))
            # execute sql delete where user_id=%d...
            if c['simulate_error'] == 2:
                raise Exception("fake rollback error")  # simulate error
            logger.info("user {} has been deleted".format(user_id))
            c['deleted_user_id'] = user_id

    def commit__create_postfix_account(context):
        logger = context['logger']
        c = context['context']
        user_name = c['user_name']
        user_email = c['user_email']
        logger.info("start create postfix account for user name={} email={}".format(user_name, user_email))
        # execute create postfix account there ...
        if c['simulate_error'] == 3:
            raise Exception("failed to create postfix account")
        c['postfix_account_created'] = True  # save variable into context
        if c['simulate_error'] == 4:
            raise Exception("fake commit error 2")  # simulate error
        logger.info("postfix account was created for user {}".format(user_email))

    def rollback__create_postfix_account(context):
        # delete user only if it has been created
        logger = context['logger']
        c = context['context']
        if 'postfix_account_created' not in c:
            # no need to rollback because account has not been created
            return
        else:
            user_email = c['user_email']
            logger.info("deleting account for user {}...".format(user_email))
            # execute postfix stuff there...
            if c['context']['simulate_error'] == 5:
                raise Exception("failed to rollback create postfix account")
            logger.info("postfix account {} has been deleted".format(user_email))
            del c['postfix_account_created']
            c['postfix_account_deleted'] = True

    def panic__create_postfix_account(context):
        try:
            logger = context['logger']
            c = context['context']
            user_email = c['user_email']
            logger.error("rollback failed, cannot delete postfix user account {}".format(user_email))
            # do some stuff there (ex: send an error email to the sys admin, ...)
            if c['simulate_error'] == 6:
                raise Exception("fake panic error, no consequence because of try/except")
        except:
            pass
        if context['context']['simulate_error'] == 7:
            raise Exception("fake critical error")  # simulate critical error

    def commit__send_grettings_email(context):
        logger = context['logger']
        c = context['context']
        user_name = c['user_name']
        user_email = c['user_email']
        logger.info("sending grettings email for user name={} email={}".format(user_name, user_email))
        # send email there ...
        if c['simulate_error'] == 8:
            raise Exception("failed to send email")
        c['grettings_email_sent'] = True  # save variable into context
        logger.info("grettings email was sent to user {}".format(user_email))

    trans_desc_scenario = [
        ('a. create user sql', commit__create_user, rollback__create_user, None),
        ('b. create user postfix', commit__create_postfix_account, rollback__create_postfix_account, panic__create_postfix_account),
        ('c. send grettings email', commit__send_grettings_email, None, None)
    ]

    trans_context = {
        'user_name': 'John Doe',
        'user_email': 'fake-email@localhost',
        'simulate_error': simulate_error
    }

    trans = Transaction(logger=logging, transaction_description=trans_desc_scenario, verbose=True)
    result = trans.run(context=trans_context)
    logging.info("end with result {}.".format(result))
    assert result is expected
    # (python 3) look at logs: init_logger.queue.queue
