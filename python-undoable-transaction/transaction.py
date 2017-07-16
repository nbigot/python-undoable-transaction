# -*- coding: utf-8 -*-

__version__ = '0.1.0'
__author__ = 'Nicolas Bigot'


class Transaction(object):
    """
    Undoable multi-step transaction
    """

    def __init__(self, logger, transaction_description, verbose=True):
        self.verbose = verbose
        self.logger = logger
        self.trans_step_steps = Transaction.validate_transaction_description(transaction_description)
        self.context = None

    @staticmethod
    def default_commit_fn(*arg, **kwargs):
        pass

    @staticmethod
    def default_rollback_fn(*arg, **kwargs):
        pass

    @staticmethod
    def default_panic_fn(*arg, **kwargs):
        pass

    @staticmethod
    def log_fn(context, level, text):
        if level.lower() == 'info':
            context['logger'].info(text)
        elif level.lower() == 'warning':
            context['logger'].warning(text)
        else:
            context['logger'].error(text)
        return True

    @staticmethod
    def validate_transaction_description(transaction_description):
        steps = []
        step_index = 0
        for step in transaction_description:
            if isinstance(step, tuple):
                label, commit_fn, rollback_fn, panic_fn = step
            elif isinstance(step, dict):
                label = step.get('label')
                commit_fn = step.get('commit')
                rollback_fn = step.get('rollback')
                panic_fn = step.get('panic')
            else:
                raise ValueError("transaction step must be tuple or dict at step {}".format(step_index))
            if label is None:
                label = "step #{}".format(step_index)
            else:
                label = str(label)
            if commit_fn is not None:
                assert callable(commit_fn)
            else:
                commit_fn = Transaction.default_commit_fn
            if rollback_fn is not None:
                assert callable(rollback_fn)
            else:
                rollback_fn = Transaction.default_rollback_fn
            if panic_fn is not None:
                assert callable(panic_fn)
            else:
                panic_fn = Transaction.default_panic_fn
            steps.append((step_index, label, commit_fn, rollback_fn, panic_fn))
            step_index += 1

        return steps

    def pre_commit(self, step_index):
        if self.verbose:
            label = self.trans_step_steps[step_index][1]
            self.logger.info("pre commit step {}: {}".format(step_index, label))

    def post_commit(self, step_index):
        if self.verbose:
            label = self.trans_step_steps[step_index][1]
            self.logger.info("post commit step {}: {}".format(step_index, label))

    def pre_rollback(self, step_index):
        if self.verbose:
            label = self.trans_step_steps[step_index][1]
            self.logger.warning("pre rollback step {}: {}".format(step_index, label))

    def post_rollback(self, step_index):
        if self.verbose:
            label = self.trans_step_steps[step_index][1]
            self.logger.warning("post rollback step {}: {}".format(step_index, label))

    def pre_panic_rollback(self, step_index, exception):
        if self.verbose:
            label = self.trans_step_steps[step_index][1]
            self.logger.error("pre panic: error in rollback function at step {}: {}".format(step_index, label))

    def post_panic_rollback(self, step_index):
        if self.verbose:
            label = self.trans_step_steps[step_index][1]
            self.logger.error("post panic: error in rollback function at step {}: {}".format(step_index, label))

    def on_begin_transaction(self):
        if self.verbose:
            self.logger.info("begin trans.")

    def on_commit_exception(self, step_index, exception):
        if self.verbose:
            self.logger.warning("error in commit function at step {}".format(step_index))

    def on_commited(self):
        if self.verbose:
            self.logger.info("end trans. (success)")
        return True

    def on_rollbacked(self):
        if self.verbose:
            self.logger.warning("end trans. (rollbacked)")
        return False

    def on_critical_error(self, step_index, exception):
        if self.verbose:
            self.logger.error("critical error: error in rollback panic function at step {}".format(step_index))
        return False

    def run(self, context=None):
        self.context = {
            'step_index': None,
            'steps': self.trans_step_steps,
            'logger': self.logger
        }
        if context:
            self.context['context'] = context

        self.on_begin_transaction()

        # commit each step of the transaction
        exception_at_commit_step_index = None
        step_index = None
        try:
            for step_index, label, commit_fn, rollback_fn, panic_fn in self.trans_step_steps:
                self.context['step_index'] = step_index
                self.pre_commit(step_index)
                commit_fn(self.context)
                self.post_commit(step_index)
        except Exception as ex:
            exception_at_commit_step_index = step_index
            self.on_commit_exception(step_index, ex)

        if exception_at_commit_step_index is None:
            return self.on_commited()

        # commit has failed so need to rollback
        step_index = None
        try:
            # rollback reverse each already commited step
            for step_index, label, commit_fn, rollback_fn, panic_fn in \
                    self.trans_step_steps[:exception_at_commit_step_index + 1][::-1]:
                try:
                    self.context['step_index'] = step_index
                    self.pre_rollback(step_index)
                    rollback_fn(self.context)
                    self.post_rollback(step_index)
                except Exception as ex:
                    # panic function must not raise exception,
                    # otherwise the transaction status will be corrupted
                    self.pre_panic_rollback(step_index, ex)
                    panic_fn(self.context)
                    self.post_panic_rollback(step_index)
        except Exception as ex:
            # should never go there :(
            return self.on_critical_error(step_index, ex)

        return self.on_rollbacked()
