# coding: utf-8
"""
Bases for OFX model classes to inherit.

``ofxtools.models`` classes correspond to OFX "Aggregates", as defined in
OFX section 1.3.9 - SGML/XML hierarchy nodes that organize data "Elements" ,
but do not themselves contain data.  In XML terminology, OFX "Aggregates" are
XML elements whose only content is other elements; they don't themselves
have text content.

Aggregates may contain other aggregates (which relationship is implemented
by the ``SubAggregate`` and ``List`` classes) and/or data-bearing
"Elements", i.e. leaf nodes, which are defined in ``ofxtools.Types``.

Names of all Aggregate classes must be ALL CAPS, following the convention of
the OFX spec, to be found in the package namespace by ``Aggregate.from_etree()``
which is called by the ``ofxtools.Parser``.
"""
# stdlib imports
import xml.etree.ElementTree as ET
from collections import OrderedDict
from copy import deepcopy


# local imports
from ofxtools.Types import Element, DateTime, String, Bool, InstanceCounterMixin
import ofxtools.models
from ofxtools.utils import pairwise
import re


class classproperty(property):
    """ Decorator that turns a classmethod into a property """

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class Aggregate:
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML/XML
    parent node that is empty of data text.
    """

    # Validation constraints used by ``validate_args()``.
    # Sequences of tuples (type str) defining mutually exclusive child tags.

    # Aggregate MAY have at most child from  `optionalMutexes``
    optionalMutexes = []
    # Aggregate MUST contain exactly one child from ``requiredMutexes``
    requiredMutexes = []

    def __init__(self, *args, **kwargs):
        """
        Positional args interepreted as list items (of variable #).
        kwargs interpreted as singular sub-elements.
        """
        self.validate_args(*args, **kwargs)

        for attr in self.spec:
            value = kwargs.pop(attr, None)
            try:
                # If attr is an element (i.e. its class is defined in
                # ``ofxtools.Types``, not defined below as ``Subaggregate``,
                # ``List``, etc.) then its value is type-converted here.
                try:
                    first10 = value[:10]
                    i8 = int(first10)
                    sa = re.split(r'\[', value)
                    if len(sa) == 2 and sa[1][-1] == ']':
                        i = sa[0].find('.')
                        if i < 0:
                            value = sa[0] + '.000[' + sa[1]
                except:
                    pass
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        self._apply_args(*args)
        self._apply_residual_kwargs(**kwargs)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        """
        Extra class-level validation constraints from the OFX spec not captured
        by class attribute validators.
        """

        def enforce_count(cls, args, kwargs, errMsg, **extra_kwargs):
            assert "mutexes" in extra_kwargs
            assert "predicate" in extra_kwargs

            for mutex in extra_kwargs["mutexes"]:
                count = sum([kwargs.get(i, None) is not None for i in mutex])
                if not extra_kwargs["predicate"](count):
                    kwargs = ", ".join(
                        ["{}={}".format(i, kwargs.get(i, None)) for i in mutex]
                    )
                    errFields = {
                        "cls": cls.__name__,
                        "kwargs": kwargs,
                        "mutex": mutex,
                        "count": count,
                    }
                    raise ValueError(errMsg.format(**errFields))

        enforce_count(cls, args, kwargs,
                      errMsg="{cls}({kwargs}): must contain at most 1 of [{mutex}] (not {count})",
                      mutexes=cls.optionalMutexes, predicate=lambda x: x <= 1)

        enforce_count(cls, args, kwargs,
                      errMsg="{cls}({kwargs}): must contain exactly 1 of [{mutex}] (not {count})",
                      mutexes=cls.requiredMutexes, predicate=lambda x: x == 1)

    def _apply_args(self, *args):
        if args:
            msg = "Aggregate {} does not define {} in spec {}"
            attrs = [arg.__class__.__name__ for arg in args]
            raise ValueError(msg.format(self.__class__.__name__, attrs, self.spec))

    def _apply_residual_kwargs(self, **kwargs):
        # Check that all kwargs have been consumed, i.e. we haven't been passed
        # any args that aren't in ``self.spec()``.
        if kwargs:
            msg = "Aggregate {} does not define {} (spec={})".format(
                self.__class__.__name__,
                str(list(kwargs.keys())),
                str(list(self.spec.keys())),
            )
            raise ValueError(msg)

    @classmethod
    def from_etree(cls, elem):
        """
        Instantiate from ``xml.etree.ElementTree.Element``.

        Look up `Aggregate`` subclass corresponding to ``Element.tag``;
        parse the Element structure into (args, kwargs) and pass those
        to the subclass __init__().
        """
        if not isinstance(elem, ET.Element):
            msg = "Bad type {} - should be xml.etree.ElementTree.Element"
            raise ValueError(msg.format(type(elem)))
        try:
            SubClass = getattr(ofxtools.models, elem.tag)
        except AttributeError:
            msg = "ofxtools.models doesn't define {}".format(elem.tag)
            raise ValueError(msg)

        # Hook to modify incoming ``ET.Element`` before conversion
        elem = SubClass.groom(elem)

        spec = list(SubClass.spec)
        listitems = SubClass.listitems

        args = []
        kwargs = {}
        specIndices = []

        for subelem in elem:
            key = subelem.tag.lower()

            if key in kwargs:
                msg = "{} contains multiple {}"
                raise ValueError(msg.format(SubClass.__name__, key))

            # If child contains text data, it's an Element; return text data.
            # Otherwise it's an Aggregate - perform type conversion
            if key in SubClass.unsupported:
                value = None
            elif subelem.text:
                value = subelem.text
            else:
                value = Aggregate.from_etree(subelem)

            try:
                idx = spec.index(key)
                specIndices.append((idx, spec[idx]))
                if key in listitems:
                    args.append(value)
                else:
                    kwargs[key] = value
            except ValueError:
                msg = "{} is not in {}".format(key, spec)  # FIXME
                raise ValueError(msg)

        # Verify that SubElements appear in the order defined by self.spec
        for (idx0, attr0), (idx1, attr1) in pairwise(specIndices):
            # Relative order of ListItems doesn't matter, but position of
            # ListItems relative to non-ListItems (and that of non-ListItems
            # relative to other non-ListItems) does matter.
            if idx1 <= idx0 and (attr0 not in listitems or attr1 not in listitems):
                msg = "{} SubElements out of order: {}"
                raise ValueError(msg.format(SubClass.__name__, [el.tag for el in elem]))

        instance = SubClass(*args, **kwargs)
        return instance

    @staticmethod
    def groom(elem):
        """
        Modify incoming ``ET.Element`` to play nice with our Python schema.

        Override in subclass.

        N.B. make sure to perform modifications on a copy.deepcopy(), in order
        to keep the input free of side effects!
        """
        return elem

    def to_etree(self):
        """
        Convert self and children to `ElementTree.Element` hierarchy
        """
        cls = self.__class__
        root = ET.Element(cls.__name__)
        for spec in self.spec:
            value = getattr(self, spec)
            if value is None:
                continue
            elif isinstance(value, Aggregate):
                child = value.to_etree()
                #  child = value.ungroom(child)
                root.append(child)
            else:
                converter = cls._superdict[spec]
                text = converter.unconvert(value)
                ET.SubElement(root, spec.upper()).text = text
        # Hook to modify `ET.ElementTree` after conversion
        return cls.ungroom(root)

    @classproperty
    @classmethod
    def _superdict(cls):
        """
        Consolidate cls.__dict__ with that of all superclasses.

        Traverse the method resolution order in reverse so that attributes
        defined on subclass override attributes defined on superclass.
        """
        d = OrderedDict()
        for base in reversed(cls.mro()):
            d.update(base.__dict__)
        return d

    @staticmethod
    def ungroom(elem):
        """
        Reverse groom() when converting back to ElementTree.

        Override in subclass.

        N.B. make sure to perform modifications on a copy.deepcopy(), in order
        to keep the input free of side effects!
        """
        return elem

    @classmethod
    def _ordered_attrs(cls, predicate):
        """
        Filter class attributes for items matching the given predicate.

        Return them as an OrderedDict in the same order they're declared in the
        class definition.

        N.B. predicate tests *values* of cls._superdict
             (not keys i.e. attribute names)
        """
        match_items = [(k, v) for k, v in cls._superdict.items() if predicate(v)]
        match_items.sort(key=lambda it: it[1]._counter)
        return OrderedDict(match_items)

    @classproperty
    @classmethod
    def spec(cls):
        """
        OrderedDict of all class attributes that are
        Elements/SubAggregates/Unsupported.

        N.B. SubAggregate is a subclass of Element.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, (Element, Unsupported)))

    @classproperty
    @classmethod
    def elements(cls):
        """
        OrderedDict of all class attributes that are Elements but not
        SubAggregates.
        """
        return cls._ordered_attrs(
            lambda v: isinstance(v, Element) and not isinstance(v, SubAggregate)
        )

    @classproperty
    @classmethod
    def subaggregates(cls):
        """
        OrderedDict of all class attributes that are SubAggregates.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, SubAggregate))

    @classproperty
    @classmethod
    def unsupported(cls):
        """
        OrderedDict of all class attributes that are Unsupported.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, Unsupported))

    @classproperty
    @classmethod
    def listitems(cls):
        """
        OrderedDict of all class attributes that are ListItems.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, ListItem))

    @property
    def _spec_repr(self):
        """
        Sequence of (name, repr()) for each non-empty attribute in the
        class ``_spec`` (see property above).

        Used by __repr__().
        """
        attrs = [
            (attr, repr(getattr(self, attr)))
            for attr in self.spec
            if getattr(self, attr) is not None
        ]
        return attrs

    def __repr__(self):
        attrs = ["{}={}".format(*attr) for attr in self._spec_repr]
        return "<{}({})>".format(self.__class__.__name__, ", ".join(attrs))

    def __getattr__(self, attr):
        """ Proxy access to attributes of SubAggregates """
        for subaggregate in self.subaggregates:
            subagg = getattr(self, subaggregate)
            try:
                return getattr(subagg, attr)
            except AttributeError:
                continue
        msg = "'{}' object has no attribute '{}'"
        raise AttributeError(msg.format(self.__class__.__name__, attr))


class SubAggregate(Element):
    """
    Aggregate that is a child of this parent Aggregate.

    SubAggregate instances appear only in the model class definitions
    (Aggregate subclasses).  Actual model instances replace these SubAggregate
    instances with the Aggregate instances to which they refer.

    The main job of a SubAggregate is to contribute to the ``spec`` of its
    parent model class.  It also validates ``__init__()`` args via its
    ``convert()`` method.
    """

    def _init(self, *args, **kwargs):
        args = list(args)
        self.type = args.pop(0)
        assert issubclass(self.type, Aggregate)
        super()._init(*args, **kwargs)

    def _convert_default(self, value):
        if not isinstance(value, self.type):
            msg = "'{}' is not an instance of {}"
            raise ValueError(msg.format(value, self.type))
        return value

    #  This doesn't get used
    #  def __repr__(self):
    #  return "<{}>".format(self.type.__name__)


class Unsupported(InstanceCounterMixin):
    """
    Null Aggregate/Element - not implemented (yet)
    """

    def __get__(self, instance, type_):
        pass

    def __set__(self, instance, value):
        pass

    def __repr__(self):
        return "<Unsupported>"


class ListItem(Element):
    """ """

    def _init(self, *args, **kwargs):
        args = list(args)
        self.type = args.pop(0)
        assert issubclass(self.type, Aggregate)
        super()._init(*args, **kwargs)

    def _convert_default(self, value):
        if not isinstance(value, self.type):
            msg = "'{}' is not an instance of {}"
            raise ValueError(msg.format(value, self.type))
        return value


class List(Aggregate, list):
    """
    Base class for OFX *LIST
    """
    def __init__(self, *args, **kwargs):
        list.__init__(self)
        super().__init__(*args, **kwargs)

    def _apply_args(self, *args):
        # Interpret positional args as contained list items (of variable #)
        for member in args:
            cls_name = member.__class__.__name__.lower()
            if cls_name not in self.listitems:
                msg = "{} can't contain {} as list item: {}"
                raise ValueError(msg.format(self.__class__.__name__, cls_name, member))
            self.append(member)

    def to_etree(self):
        """
        Convert self and children to `ElementTree.Element` hierarchy
        """
        cls = self.__class__
        root = ET.Element(cls.__name__)
        # Append items enumerated in the class definition
        # (i.e. direct child Elements of the *LIST defined in the OFX spec)
        # - this is used by subclasses (e.g. Tranlist), not directly by List
        for spec in self.spec:
            value = getattr(self, spec)
            if value is not None:
                converter = cls._superdict[spec]
                text = converter.unconvert(value)
                ET.SubElement(root, spec.upper()).text = text

        # Append list items
        for member in self:
            root.append(member.to_etree())
        return root

    def __hash__(self):
        """
        HACK - as a subclass of list, List is unhashable, but we need to
        use it as a dict key in Type.Element.{__get__, __set__}
        """
        return object.__hash__(self)

    def __repr__(self):
        return "<{} len={}>".format(self.__class__.__name__, len(self))
