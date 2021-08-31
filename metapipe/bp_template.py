from inspect import Parameter, Signature

from mne_bids import BIDSPath  # type: ignore


class FrozenBIDSPath:
    """(Pseudo) read-only version of BIDSPath"""
    def __init__(self, *pargs, check=False, **kwargs):
        self._bp = BIDSPath(*pargs, check=check, **kwargs)

    def update(self, *, check=None, **kwargs):
        copy = self.__class__(subject="dummy", check=False)
        copy._bp = self._bp.copy().update(**kwargs)
        return copy

    def copy(self):
        return self

    def __getattr__(self, attr):
        return getattr(self._bp, attr)

    def __repr__(self):
        return repr(self._bp).replace(
            type(self._bp).__name__, type(self).__name__
        )

    def __str__(self):
        return str(self._bp).replace(
            type(self._bp).__name__, type(self).__name__
        )

    def __dir__(self):
        own_dir = dir(type(self)) + list(self.__dict__.keys())
        return own_dir + [
            d
            for d in dir(self._bp)
            if not d.startswith("_") and d not in own_dir
        ]

    def __fspath__(self):
        return self._bp.__fspath__()

    def __eq__(self, other):
        return self._bp.__eq__(other)

    def __ne__(self, other):
        return self._bp.__ne__(other)


class BIDSPathTemplate(FrozenBIDSPath):
    def __init__(self, *pargs, check=False, template_vars=None, **kwargs):
        self._check = check
        template_vars = set() if template_vars is None else template_vars
        super().__init__(*pargs, check=check, **kwargs)
        self._template_vars = set(template_vars)
        for var in self._template_vars:
            self._check_template_var(var)
        self._make_fpath_signature()

    def fpath(self, **kwargs):
        # based on recipie 9.16 from the Python Cookbook, 3-d edition
        self._fpath_sig.bind(**kwargs)

        concrete_bp = self.update(**kwargs, check=self._check)
        return super(self.__class__, concrete_bp).__getattr__("fpath")

    def update(self, *, check: bool = None, **kwargs):
        """
        Note
        ----
        When updating BIDS key-value pairs (not template_vars),
        if some of the keys were present template_vars and updated to non-None
        values, these keys are removed from template_vars

        """
        if "template_vars" in kwargs:
            other_template_vars = set(kwargs.pop("template_vars"))
        else:
            other_template_vars = self._template_vars.copy()

        self._check = check
        other = super().update(check=check, **kwargs)
        for key, val in kwargs.items():
            if key in self._template_vars:
                other_template_vars.remove(key)
        other._template_vars = other_template_vars
        other._make_fpath_signature()
        return other

    @property
    def template_vars(self):
        return self._template_vars

    def _make_fpath_signature(self):
        params = [
            Parameter(p, Parameter.KEYWORD_ONLY) for p in self._template_vars
        ]
        self._fpath_sig = Signature(params)

    def _check_template_var(self, var):
        if var not in self.entities:
            raise ValueError(
                "Template entities should be in"
                f"{list(self.entities)}; got '{var}'"
            )
        if self.entities[var] is not None:
            raise ValueError(
                "Can only set 'None' entities as the template ones"
                f" ({var} is set to '{self.entities[var]}')"
            )
