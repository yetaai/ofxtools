# coding: utf-8
""" Unit tests for ofxtools.models.seclist """

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy


# local imports
from ofxtools.utils import UTC
from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.invest.securities import (
    SECID,
    SECINFO,
    DEBTINFO,
    MFINFO,
    OPTINFO,
    OTHERINFO,
    STOCKINFO,
    PORTION,
    FIPORTION,
    MFASSETCLASS,
    FIMFASSETCLASS,
    ASSETCLASSES,
    SECLIST,
    SECRQ,
    SECLISTRQ,
    SECLISTRS,
)


# test imports
import base
from test_models_i18n import CurrencyTestCase


class SecidTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("UNIQUEID", "UNIQUEIDTYPE")

    @property
    def root(self):
        root = Element("SECID")
        SubElement(root, "UNIQUEID").text = "084670108"
        SubElement(root, "UNIQUEIDTYPE").text = "CUSIP"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECID)
        self.assertEqual(root.uniqueid, "084670108")
        self.assertEqual(root.uniqueidtype, "CUSIP")


class SecinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("SECID", "SECNAME")
    optionalElements = ("TICKER", "FIID", "RATING", "UNITPRICE", "DTASOF", "CURRENCY")

    @property
    def root(self):
        root = Element("SECINFO")
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "SECNAME").text = "Acme Development, Inc."
        SubElement(root, "TICKER").text = "ACME"
        SubElement(root, "FIID").text = "AC.ME"
        SubElement(root, "RATING").text = "Aa"
        SubElement(root, "UNITPRICE").text = "94.5"
        SubElement(root, "DTASOF").text = "20130615"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "MEMO").text = "Foobar"
        return root

    def testConvertSecnameTooLong(self):
        """ Don't enforce length restriction on SECNAME; raise Warning """
        # Issue #12
        copy_root = deepcopy(self.root)
        copy_element = Element("SECNAME")
        copy_element.text = """
        There is a theory going around that the U.S.A. was and still is a
        gigantic Masonic plot under the ultimate control of the group known as
        the Illuminati. It is difficult to look for long at the strange single
        eye crowning the pyramid which is found on every dollar bill and not
        begin to believe the story, a little. Too many anarchists in
        19th-century Europe — Bakunin, Proudhon, Salverio Friscia — were Masons
        for it to be pure chance. Lovers of global conspiracy, not all of them
        Catholic, can count on the Masons for a few good shivers and voids when
        all else fails.
        """
        copy_root[1] = copy_element
        with self.assertWarns(Warning):
            root = Aggregate.from_etree(copy_root)
        self.assertEqual(
            root.secname,
            """
        There is a theory going around that the U.S.A. was and still is a
        gigantic Masonic plot under the ultimate control of the group known as
        the Illuminati. It is difficult to look for long at the strange single
        eye crowning the pyramid which is found on every dollar bill and not
        begin to believe the story, a little. Too many anarchists in
        19th-century Europe — Bakunin, Proudhon, Salverio Friscia — were Masons
        for it to be pure chance. Lovers of global conspiracy, not all of them
        Catholic, can count on the Masons for a few good shivers and voids when
        all else fails.
        """,
        )

    def testConvertTickerTooLong(self):
        """ Don't enforce length restriction on TICKER; raise Warning """
        # Issue #12
        copy_root = deepcopy(self.root)
        copy_element = Element("TICKER")
        copy_element.text = """
        Kekulé dreams the Great Serpent holding its own tail in its mouth, the
        dreaming Serpent which surrounds the World.  But the meanness, the
        cynicism with which this dream is to be used. The Serpent that
        announces, "The World is a closed thing, cyclical, resonant,
        eternally-returning," is to be delivered into a system whose only aim
        is to violate the Cycle. Taking and not giving back, demanding that
        "productivity" and "earnings" keep on increasing with time, the System
        removing from the rest of the World these vast quantities of energy to
        keep its own tiny desperate fraction showing a profit: and not only
        most of humanity — most of the World, animal, vegetable, and mineral,
        is laid waste in the process. The System may or may not understand that
        it's only buying time. And that time is an artificial resource to begin
        with, of no value to anyone or anything but the System, which must
        sooner or later crash to its death, when its addiction to energy has
        become more than the rest of the World can supply, dragging with it
        innocent souls all along the chain of life.
        """
        copy_root[2] = copy_element
        with self.assertWarns(Warning):
            root = Aggregate.from_etree(copy_root)
        self.assertEqual(
            root.ticker,
            """
        Kekulé dreams the Great Serpent holding its own tail in its mouth, the
        dreaming Serpent which surrounds the World.  But the meanness, the
        cynicism with which this dream is to be used. The Serpent that
        announces, "The World is a closed thing, cyclical, resonant,
        eternally-returning," is to be delivered into a system whose only aim
        is to violate the Cycle. Taking and not giving back, demanding that
        "productivity" and "earnings" keep on increasing with time, the System
        removing from the rest of the World these vast quantities of energy to
        keep its own tiny desperate fraction showing a profit: and not only
        most of humanity — most of the World, animal, vegetable, and mineral,
        is laid waste in the process. The System may or may not understand that
        it's only buying time. And that time is an artificial resource to begin
        with, of no value to anyone or anything but the System, which must
        sooner or later crash to its death, when its addiction to energy has
        become more than the rest of the World can supply, dragging with it
        innocent souls all along the chain of life.
        """,
        )

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)


class DebtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("SECINFO", "PARVALUE", "DEBTTYPE")
    optionalElements = (
        "DEBTCLASS",
        "COUPONRT",
        "DTCOUPON",
        "COUPONFREQ",
        "CALLPRICE",
        "YIELDTOCALL",
        "DTCALL",
        "CALLTYPE",
        "YIELDTOMAT",
        "DTMAT",
        "ASSETCLASS",
        "FIASSETCLASS",
    )

    @property
    def root(self):
        root = Element("DEBTINFO")
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, "PARVALUE").text = "1000"
        SubElement(root, "DEBTTYPE").text = "COUPON"
        SubElement(root, "DEBTCLASS").text = "CORPORATE"
        SubElement(root, "COUPONRT").text = "5.125"
        SubElement(root, "DTCOUPON").text = "20031201"
        SubElement(root, "COUPONFREQ").text = "QUARTERLY"
        SubElement(root, "CALLPRICE").text = "1000"
        SubElement(root, "YIELDTOCALL").text = "6.5"
        SubElement(root, "DTCALL").text = "20051215"
        SubElement(root, "CALLTYPE").text = "CALL"
        SubElement(root, "YIELDTOMAT").text = "6.0"
        SubElement(root, "DTMAT").text = "20061215"
        SubElement(root, "ASSETCLASS").text = "INTLBOND"
        SubElement(root, "FIASSETCLASS").text = "Fixed to floating bond"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, DEBTINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.parvalue, Decimal("1000"))
        self.assertEqual(root.debttype, "COUPON")
        self.assertEqual(root.debtclass, "CORPORATE")
        self.assertEqual(root.couponrt, Decimal("5.125"))
        self.assertEqual(root.dtcoupon, datetime(2003, 12, 1, tzinfo=UTC))
        self.assertEqual(root.couponfreq, "QUARTERLY")
        self.assertEqual(root.callprice, Decimal("1000"))
        self.assertEqual(root.yieldtocall, Decimal("6.5"))
        self.assertEqual(root.dtcall, datetime(2005, 12, 15, tzinfo=UTC))
        self.assertEqual(root.calltype, "CALL")
        self.assertEqual(root.yieldtomat, Decimal("6.0"))
        self.assertEqual(root.dtmat, datetime(2006, 12, 15, tzinfo=UTC))
        self.assertEqual(root.assetclass, "INTLBOND")
        self.assertEqual(root.fiassetclass, "Fixed to floating bond")

    def testOneOf(self):
        self.oneOfTest("DEBTTYPE", ("COUPON", "ZERO"))
        self.oneOfTest("DEBTCLASS", ("TREASURY", "MUNICIPAL", "CORPORATE", "OTHER"))
        self.oneOfTest(
            "COUPONFREQ", ("MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL", "OTHER")
        )
        self.oneOfTest("CALLTYPE", ("CALL", "PUT", "PREFUND", "MATURITY"))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class PortionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PORTION")
        SubElement(root, "ASSETCLASS").text = "DOMESTICBOND"
        SubElement(root, "PERCENT").text = "15"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PORTION)
        self.assertEqual(root.assetclass, "DOMESTICBOND")
        self.assertEqual(root.percent, Decimal("15"))

    def testOneOf(self):
        self.oneOfTest("ASSETCLASS", ASSETCLASSES)


class MfassetclassTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    # requiredElements = ('PORTION',)  # FIXME - how to handle multiple PORTIONs?

    @property
    def root(self):
        root = Element("MFASSETCLASS")
        for i in range(4):
            portion = PortionTestCase().root
            root.append(portion)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFASSETCLASS)
        self.assertEqual(len(root), 4)
        for i in range(4):
            self.assertIsInstance(root[i], PORTION)


class FiportionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("FIPORTION")
        SubElement(root, "FIASSETCLASS").text = "Foobar"
        SubElement(root, "PERCENT").text = "50"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FIPORTION)
        self.assertEqual(root.fiassetclass, "Foobar")
        self.assertEqual(root.percent, Decimal("50"))


class FimfassetclassTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    # requiredElements = ('FIPORTION',)  # FIXME - how to handle multiple FIPORTIONs?

    @property
    def root(self):
        root = Element("FIMFASSETCLASS")
        for i in range(4):
            portion = FiportionTestCase().root
            root.append(portion)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FIMFASSETCLASS)
        self.assertEqual(len(root), 4)
        for i in range(4):
            self.assertIsInstance(root[i], FIPORTION)


class MfinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("SECINFO",)
    optionalElements = (
        "MFTYPE",
        "YIELD",
        "DTYIELDASOF",
        "MFASSETCLASS",
        "FIMFASSETCLASS",
    )

    @property
    def root(self):
        root = Element("MFINFO")
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, "MFTYPE").text = "OPENEND"
        SubElement(root, "YIELD").text = "5.0"
        SubElement(root, "DTYIELDASOF").text = "20030501"
        mfassetclass = MfassetclassTestCase().root
        root.append(mfassetclass)
        fimfassetclass = FimfassetclassTestCase().root
        root.append(fimfassetclass)
        return root

    def testOneOf(self):
        self.oneOfTest("MFTYPE", ("OPENEND", "CLOSEEND", "OTHER"))

    def testGroom(self):
        root = deepcopy(self.root)
        root = MFINFO.groom(root)
        self.assertIsInstance(root, Element)
        self.assertEqual(len(root), len(self.root))
        secinfo, mftype, yld, dtyieldasof, mfassetclass, fimfassetclass = root[:]

        # FIXME - test the other children too
        self.assertIsInstance(yld, Element)
        self.assertEqual(len(yld), 0)
        self.assertEqual(yld.tag, "YLD")
        self.assertEqual(yld.text, "5.0")

    def testUngroom(self):
        root = self.root
        yld = root[2]
        yld.tag = "YLD"
        root = MFINFO.ungroom(root)
        yld = root[2]
        self.assertEqual(yld.tag, "YIELD")

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.mftype, "OPENEND")
        self.assertEqual(root.yld, Decimal("5.0"))
        self.assertEqual(root.dtyieldasof, datetime(2003, 5, 1, tzinfo=UTC))
        self.assertIsInstance(root.mfassetclass, MFASSETCLASS)
        self.assertIsInstance(root.fimfassetclass, FIMFASSETCLASS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class OptinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("SECINFO", "OPTTYPE", "STRIKEPRICE", "DTEXPIRE", "SHPERCTRCT")
    optionalElements = ("SECID", "ASSETCLASS", "FIASSETCLASS")

    @property
    def root(self):
        root = Element("OPTINFO")
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, "OPTTYPE").text = "CALL"
        SubElement(root, "STRIKEPRICE").text = "25.5"
        SubElement(root, "DTEXPIRE").text = "20031215"
        SubElement(root, "SHPERCTRCT").text = "100"
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "ASSETCLASS").text = "SMALLSTOCK"
        SubElement(root, "FIASSETCLASS").text = "FOO"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OPTINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.opttype, "CALL")
        self.assertEqual(root.strikeprice, Decimal("25.5"))
        self.assertEqual(root.dtexpire, datetime(2003, 12, 15, tzinfo=UTC))
        self.assertEqual(root.shperctrct, 100)
        self.assertEqual(root.assetclass, "SMALLSTOCK")
        self.assertEqual(root.fiassetclass, "FOO")

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class OtherinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("SECINFO",)
    optionalElements = ("TYPEDESC", "ASSETCLASS", "FIASSETCLASS")

    @property
    def root(self):
        root = Element("OTHERINFO")
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, "TYPEDESC").text = "Securitized baseball card pool"
        SubElement(root, "ASSETCLASS").text = "SMALLSTOCK"
        SubElement(root, "FIASSETCLASS").text = "FOO"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OTHERINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.typedesc, "Securitized baseball card pool")
        self.assertEqual(root.assetclass, "SMALLSTOCK")
        self.assertEqual(root.fiassetclass, "FOO")

    def testOneOf(self):
        self.oneOfTest("ASSETCLASS", ASSETCLASSES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class StockinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("SECINFO",)
    optionalElements = (
        "STOCKTYPE",
        "YIELD",
        "DTYIELDASOF",
        "ASSETCLASS",
        "FIASSETCLASS",
    )

    @property
    def root(self):
        root = Element("STOCKINFO")
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, "STOCKTYPE").text = "CONVERTIBLE"
        SubElement(root, "YIELD").text = "5.0"
        SubElement(root, "DTYIELDASOF").text = "20030501"
        SubElement(root, "ASSETCLASS").text = "SMALLSTOCK"
        SubElement(root, "FIASSETCLASS").text = "FOO"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STOCKINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.stocktype, "CONVERTIBLE")
        self.assertEqual(root.yld, Decimal("5.0"))
        self.assertEqual(root.dtyieldasof, datetime(2003, 5, 1, tzinfo=UTC))
        self.assertEqual(root.assetclass, "SMALLSTOCK")
        self.assertEqual(root.fiassetclass, "FOO")

    def testGroom(self):
        root = deepcopy(self.root)
        root = STOCKINFO.groom(root)
        self.assertIsInstance(root, Element)
        self.assertEqual(len(root), len(self.root))
        secinfo, stocktype, yld, dtyieldasof, assetclass, fiassetclass = root[:]

        # FIXME - test the other children too
        self.assertIsInstance(yld, Element)
        self.assertEqual(len(yld), 0)
        self.assertEqual(yld.tag, "YLD")
        self.assertEqual(yld.text, "5.0")

    def testUngroom(self):
        root = self.root
        yld = root[2]
        yld.tag = "YLD"
        root = STOCKINFO.ungroom(root)
        yld = root[2]
        self.assertEqual(yld.tag, "YIELD")

    def testOneOf(self):
        self.oneOfTest("ASSETCLASS", ASSETCLASSES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class SeclistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = []  # FIXME - how to handle SECINFO subclasses?

    @property
    def root(self):
        root = Element("SECLIST")
        secinfo = DebtinfoTestCase().root
        root.append(secinfo)
        secinfo = MfinfoTestCase().root
        root.append(secinfo)
        secinfo = OptinfoTestCase().root
        root.append(secinfo)
        secinfo = OtherinfoTestCase().root
        root.append(secinfo)
        secinfo = StockinfoTestCase().root
        root.append(secinfo)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLIST)
        self.assertEqual(len(root), 5)
        self.assertIsInstance(root[0], DEBTINFO)
        self.assertIsInstance(root[1], MFINFO)
        self.assertIsInstance(root[2], OPTINFO)
        self.assertIsInstance(root[3], OTHERINFO)
        self.assertIsInstance(root[4], STOCKINFO)


class SecrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def emptyBase(cls):
        return Element("SECRQ")

    @classproperty
    @classmethod
    def validSoup(cls):
        secid = SecidTestCase().root
        ticker = Element("TICKER")
        ticker.text = "ABCD"
        fiid = Element("FIID")
        fiid.text = "A1B2C3D4"

        for choice in secid, ticker, fiid:
            root = cls.emptyBase
            root.append(choice)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [('secid', 'ticker', 'fiid')]
        secid = SecidTestCase().root
        ticker = Element("TICKER")
        ticker.text = "ABCD"
        fiid = Element("FIID")
        fiid.text = "A1B2C3D4"

        #  None
        root = cls.emptyBase
        yield root

        #  Two
        for (choice0, choice1) in [(secid, ticker), (secid, fiid), (ticker, fiid)]:
            root = cls.emptyBase
            root.append(choice0)
            root.append(choice1)
            yield root

        # All three
        root = cls.emptyBase
        root.append(secid)
        root.append(ticker)
        root.append(fiid)
        yield root

        #  FIXME
        #  Check out-of-order errors

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class SeclistrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SECLISTRQ")
        for i in range(2):
            root.append(SecrqTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SECLISTRQ)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], SECRQ)
        self.assertIsInstance(instance[1], SECRQ)


class SeclistrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        return Element("SECLISTRS")

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SECLISTRS)
        self.assertEqual(len(instance.spec), 0)


class SeclisttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = SeclistrqTestCase


class SeclisttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = SeclistrsTestCase


if __name__ == "__main__":
    unittest.main()
